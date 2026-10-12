# -*- coding: utf-8 -*-
"""
Kite Connect Authentication Manager
Handles session management and token refresh
"""

from kiteconnect import KiteConnect
from utils.logger import TradingLogger
import json
import os
from datetime import datetime


class AuthenticationManager:
    """
    Manages Kite Connect authentication and session.
    Handles login, token refresh, and session persistence.
    """

    def __init__(self, api_key, api_secret, redirect_url="http://localhost:5000/callback"):
        """
        Initialize authentication manager.
        
        Args:
            api_key: str - Your Kite API key
            api_secret: str - Your Kite API secret
            redirect_url: str - OAuth redirect URL
        """
        self.api_key = api_key
        self.api_secret = api_secret
        self.redirect_url = redirect_url
        self.kite = None
        self.logger = TradingLogger.get_logger()
        self.session_file = ".kite_session.json"

    def get_login_url(self):
        """
        Get the Kite login URL for OAuth authentication.
        
        Returns:
            str - Login URL to redirect user to
        """
        kite = KiteConnect(api_key=self.api_key)
        login_url = kite.login_url()
        self.logger.info(f"Login URL: {login_url}")
        return login_url

    def create_session(self, request_token):
        """
        Create a session using request token from login.
        
        Args:
            request_token: str - Token obtained from login redirect
            
        Returns:
            dict - Session data with access token and user info
        """
        try:
            kite = KiteConnect(api_key=self.api_key)
            session_data = kite.generate_session(request_token, self.api_secret)
            
            # Store the Kite instance
            self.kite = kite
            
            # Save session for later use
            self._save_session(session_data)
            
            self.logger.info(f"Session created successfully for {session_data.get('user_name')}")
            return session_data
        
        except Exception as e:
            self.logger.error(f"Failed to create session: {str(e)}")
            raise

    def restore_session(self, access_token):
        """
        Restore a session using saved access token.
        
        Args:
            access_token: str - Previously saved access token
            
        Returns:
            KiteConnect instance
        """
        try:
            kite = KiteConnect(api_key=self.api_key, access_token=access_token)
            
            # Verify token is valid by making a test call
            profile = kite.profile()
            self.kite = kite
            
            self.logger.info(f"Session restored for {profile.get('user_name')}")
            return kite
        
        except Exception as e:
            self.logger.error(f"Failed to restore session: {str(e)}")
            raise

    def get_kite_instance(self):
        """
        Get the active Kite Connect instance.
        
        Returns:
            KiteConnect instance
        """
        if self.kite is None:
            self.logger.error("No active session. Please authenticate first.")
            raise ValueError("Not authenticated. Call create_session() or restore_session() first.")
        return self.kite

    def _save_session(self, session_data):
        """
        Save session data locally for future use.
        
        Args:
            session_data: dict - Session data from generate_session()
        """
        try:
            with open(self.session_file, 'w') as f:
                json.dump({
                    "access_token": session_data.get("access_token"),
                    "refresh_token": session_data.get("refresh_token"),
                    "saved_at": datetime.now().isoformat(),
                    "user_name": session_data.get("user_name"),
                }, f)
            self.logger.info("Session saved locally")
        except Exception as e:
            self.logger.warning(f"Could not save session: {str(e)}")

    def load_saved_session(self):
        """
        Load previously saved session from file.
        
        Returns:
            dict - Saved session data or None
        """
        if os.path.exists(self.session_file):
            try:
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                return session_data
            except Exception as e:
                self.logger.warning(f"Could not load saved session: {str(e)}")
        return None
