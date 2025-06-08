#!/usr/bin/env python3
# PROJECT PALIOXIS: Pluggable Destroyer Modules
# This file contains the base class and implementations for various file destruction methods

import os
import abc
import subprocess
import logging
import platform
from typing import List, Optional

class BaseDestroyer(abc.ABC):
    """Abstract base class for all destroyer implementations"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.logger = logging.getLogger('palioxis.destroyer')
    
    @abc.abstractmethod
    def destroy_file(self, filepath: str) -> bool:
        """Destroy a single file securely"""
        pass
    
    def destroy_dir(self, dirpath: str) -> bool:
        """Recursively destroy all files in a directory"""
        try:
            self.logger.info(f"Starting destruction of directory: {dirpath}")
            success = True
            
            for root, dirs, files in os.walk(dirpath, topdown=False):
                # First destroy all files in the directory
                for file in files:
                    full_path = os.path.join(root, file)
                    if not self.destroy_file(full_path):
                        self.logger.error(f"Failed to destroy file: {full_path}")
                        success = False
                
                # Then try to remove the empty directories
                for dir in dirs:
                    try:
                        full_dir = os.path.join(root, dir)
                        os.rmdir(full_dir)
                        self.logger.debug(f"Removed directory: {full_dir}")
                    except OSError as e:
                        self.logger.error(f"Failed to remove directory {full_dir}: {e}")
                        success = False
            
            # Finally try to remove the root directory itself
            try:
                os.rmdir(dirpath)
                self.logger.debug(f"Removed root directory: {dirpath}")
            except OSError as e:
                self.logger.error(f"Failed to remove root directory {dirpath}: {e}")
                success = False
                
            return success
        except Exception as e:
            self.logger.error(f"Error destroying directory {dirpath}: {e}")
            return False
    
    def destroy_paths(self, paths: List[str]) -> bool:
        """Destroy a list of files or directories"""
        overall_success = True
        for path in paths:
            if not path or not os.path.exists(path):
                self.logger.warning(f"Path does not exist: {path}")
                continue
                
            try:
                if os.path.isfile(path):
                    if not self.destroy_file(path):
                        overall_success = False
                elif os.path.isdir(path):
                    if not self.destroy_dir(path):
                        overall_success = False
                else:
                    self.logger.warning(f"Path is neither file nor directory: {path}")
            except Exception as e:
                self.logger.error(f"Error processing path {path}: {e}")
                overall_success = False
                
        return overall_success


class ShredDestroyer(BaseDestroyer):
    """Destroyer implementation using the 'shred' command"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.passes = int(self.config.get('shred_passes', 9))
        
    def destroy_file(self, filepath: str) -> bool:
        """Securely destroy a file using the shred command"""
        try:
            self.logger.debug(f"Shredding file: {filepath}")
            cmd = ['shred', '-n', str(self.passes), '-z', '-f', '-u', filepath]
            subprocess.run(cmd, check=True)
            self.logger.debug(f"Successfully shredded file: {filepath}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Shred command failed for {filepath}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error shredding file {filepath}: {e}")
            return False


class FastDestroyer(BaseDestroyer):
    """Fast destroyer implementation using Python's native file operations"""
    
    def __init__(self, config=None):
        super().__init__(config)
        self.passes = int(self.config.get('fast_passes', 3))
        
    def destroy_file(self, filepath: str) -> bool:
        """Overwrite file with random data and then delete it"""
        try:
            if not os.path.exists(filepath) or not os.path.isfile(filepath):
                self.logger.warning(f"File does not exist: {filepath}")
                return True  # Not an error if file doesn't exist
            
            # Get the file size
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                # Just delete empty files
                os.remove(filepath)
                return True
                
            self.logger.debug(f"Fast destroying file: {filepath} ({file_size} bytes)")
            
            # Perform the overwrite passes
            for i in range(self.passes):
                with open(filepath, 'wb') as f:
                    # Write in chunks to handle large files
                    chunk_size = min(1024 * 1024, file_size)  # 1MB chunks or file size
                    remaining = file_size
                    
                    while remaining > 0:
                        write_size = min(chunk_size, remaining)
                        f.write(os.urandom(write_size))
                        remaining -= write_size
            
            # Delete the file after overwriting
            os.remove(filepath)
            self.logger.debug(f"Successfully destroyed file: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error fast-destroying file {filepath}: {e}")
            return False


class WipeDestroyer(BaseDestroyer):
    """Destroyer implementation using the 'wipe' command"""
    
    def destroy_file(self, filepath: str) -> bool:
        """Securely destroy a file using the wipe command"""
        try:
            self.logger.debug(f"Wiping file: {filepath}")
            cmd = ['wipe', '-rf', filepath]
            subprocess.run(cmd, check=True)
            self.logger.debug(f"Successfully wiped file: {filepath}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Wipe command failed for {filepath}: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error wiping file {filepath}: {e}")
            return False


class WindowsDestroyer(BaseDestroyer):
    """Destroyer implementation for Windows systems"""
    
    def destroy_file(self, filepath: str) -> bool:
        """Securely destroy a file using Windows-specific methods"""
        try:
            self.logger.debug(f"Destroying file with Windows method: {filepath}")
            
            # First overwrite the file
            file_size = os.path.getsize(filepath)
            if file_size > 0:
                with open(filepath, 'wb') as f:
                    f.write(os.urandom(file_size))
            
            # Then use the cipher command if available
            try:
                dir_path = os.path.dirname(filepath)
                cmd = ['cipher', '/w:' + dir_path]
                subprocess.run(cmd, check=True)
            except subprocess.SubprocessError:
                self.logger.warning("Cipher command failed, falling back to basic deletion")
                
            # Finally remove the file
            os.remove(filepath)
            self.logger.debug(f"Successfully destroyed file: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"Error destroying file with Windows method {filepath}: {e}")
            return False


def get_destroyer(module_name: str, config=None) -> BaseDestroyer:
    """Factory function to create the appropriate destroyer instance"""
    destroyers = {
        'shred': ShredDestroyer,
        'fast': FastDestroyer,
        'wipe': WipeDestroyer,
        'windows': WindowsDestroyer
    }
    
    if module_name.lower() not in destroyers:
        logging.warning(f"Destroyer module '{module_name}' not recognized, falling back to 'fast'")
        module_name = 'fast'
        
    # If on Windows and using 'shred' or 'wipe', they won't be available
    if platform.system() == 'Windows' and module_name.lower() in ['shred', 'wipe']:
        logging.warning(f"Destroyer module '{module_name}' not available on Windows, using 'windows'")
        module_name = 'windows'
        
    destroyer_class = destroyers[module_name.lower()]
    return destroyer_class(config)
