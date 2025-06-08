#!/usr/bin/env python3
# PROJECT PALIOXIS: Configuration Manager
# This file handles loading and parsing of the configuration file

import os
import sys
import logging
import configparser
from typing import List, Dict, Any, Optional

class ConfigManager:
    """Handles loading and accessing configuration settings"""
    
    def __init__(self, config_file_path: Optional[str] = None):
        """Initialize with optional explicit config file path"""
        self.config = configparser.ConfigParser(allow_no_value=True)
        self.config_file = config_file_path
        self.logger = logging.getLogger('palioxis.config')
        
    def load_config(self) -> bool:
        """Load the configuration file"""
        # Default search paths for the config file
        search_paths = [
            self.config_file,  # Explicit path if provided
            'palioxis.conf',   # Current directory
            os.path.expanduser('~/.palioxis.conf'),  # User's home directory
            '/etc/palioxis.conf'  # System-wide config
        ]
        
        # Filter out None entries (if config_file wasn't specified)
        search_paths = [p for p in search_paths if p]
        
        config_found = False
        for path in search_paths:
            try:
                if os.path.exists(path):
                    self.logger.info(f"Loading configuration from {path}")
                    self.config.read(path)
                    self.config_file = path
                    config_found = True
                    break
            except Exception as e:
                self.logger.error(f"Error loading configuration from {path}: {e}")
                
        if not config_found:
            self.logger.warning("No configuration file found, using defaults")
            self._create_default_config()
            
        return config_found
    
    def _create_default_config(self) -> None:
        """Create a default configuration if no file is found"""
        # Set up default sections
        self.config['Server'] = {
            'host': '0.0.0.0',
            'port': '8443',
            'key': 'OHSNAP'
        }
        self.config['Certificates'] = {
            'ca_cert': 'palioxis-ca.crt',
            'server_cert': 'palioxis-server.crt',
            'server_key': 'palioxis-server.key',
            'client_cert': 'palioxis-client.crt',
            'client_key': 'palioxis-client.key'
        }
        self.config['Destroyer'] = {
            'module': 'fast',
            'fast_passes': '3',
            'shred_passes': '9'
        }
        self.config['Daemon'] = {
            'log_file': 'palioxis.log',
            'log_level': 'INFO'
        }
        self.config['Targets'] = {}
        self.config['Client'] = {
            'nodes_list': 'nodes.txt'
        }
    
    def save_config(self, path: Optional[str] = None) -> bool:
        """Save current configuration to a file"""
        save_path = path or self.config_file or 'palioxis.conf'
        try:
            with open(save_path, 'w') as configfile:
                self.config.write(configfile)
            self.logger.info(f"Configuration saved to {save_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save configuration to {save_path}: {e}")
            return False
        
    def get(self, section: str, option: str, default: Any = None) -> str:
        """Get a configuration value, with a default if not found"""
        try:
            return self.config.get(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
            
    def get_int(self, section: str, option: str, default: int = 0) -> int:
        """Get an integer configuration value, with a default if not found"""
        try:
            return self.config.getint(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
            
    def get_bool(self, section: str, option: str, default: bool = False) -> bool:
        """Get a boolean configuration value, with a default if not found"""
        try:
            return self.config.getboolean(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
            
    def get_float(self, section: str, option: str, default: float = 0.0) -> float:
        """Get a float configuration value, with a default if not found"""
        try:
            return self.config.getfloat(section, option)
        except (configparser.NoSectionError, configparser.NoOptionError, ValueError):
            return default
            
    def get_list(self, section: str, option: str) -> List[str]:
        """Get a list of values from a multi-line configuration option"""
        try:
            value = self.config.get(section, option)
            return [line.strip() for line in value.strip().split('\n') if line.strip()]
        except (configparser.NoSectionError, configparser.NoOptionError):
            return []
            
    def get_target_directories(self) -> List[str]:
        """Get the list of target directories for destruction"""
        try:
            if self.config.has_option('Targets', 'directories'):
                return self.get_list('Targets', 'directories')
            
            # If no directories in config, try to read from targets.txt
            if os.path.exists('targets.txt'):
                with open('targets.txt', 'r') as f:
                    return [line.strip() for line in f.readlines() if line.strip()]
            
            return []
        except Exception as e:
            self.logger.error(f"Error getting target directories: {e}")
            return []
            
    def get_server_settings(self) -> Dict[str, Any]:
        """Get all server-related settings as a dictionary"""
        return {
            'host': self.get('Server', 'host', '0.0.0.0'),
            'port': self.get_int('Server', 'port', 8443),
            'key': self.get('Server', 'key', 'OHSNAP'),
            'ca_cert': self.get('Certificates', 'ca_cert', 'palioxis-ca.crt'),
            'server_cert': self.get('Certificates', 'server_cert', 'palioxis-server.crt'),
            'server_key': self.get('Certificates', 'server_key', 'palioxis-server.key')
        }
        
    def get_client_settings(self) -> Dict[str, Any]:
        """Get all client-related settings as a dictionary"""
        return {
            'nodes_list': self.get('Client', 'nodes_list', 'nodes.txt'),
            'ca_cert': self.get('Certificates', 'ca_cert', 'palioxis-ca.crt'),
            'client_cert': self.get('Certificates', 'client_cert', 'palioxis-client.crt'),
            'client_key': self.get('Certificates', 'client_key', 'palioxis-client.key')
        }
        
    def get_destroyer_settings(self) -> Dict[str, Any]:
        """Get all destroyer-related settings as a dictionary"""
        return {
            'module': self.get('Destroyer', 'module', 'fast'),
            'fast_passes': self.get_int('Destroyer', 'fast_passes', 3),
            'shred_passes': self.get_int('Destroyer', 'shred_passes', 9)
        }
        
    def get_daemon_settings(self) -> Dict[str, Any]:
        """Get all daemon-related settings as a dictionary"""
        return {
            'log_file': self.get('Daemon', 'log_file', 'palioxis.log'),
            'log_level': self.get('Daemon', 'log_level', 'INFO')
        }

    def update(self, section: str, option: str, value: Any) -> None:
        """Update a configuration value"""
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, option, str(value))
