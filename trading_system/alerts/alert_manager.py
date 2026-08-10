# -*- coding: utf-8 -*-
"""
Alert System for Email and SMS Notifications
Send alerts for trades, positions, and performance events
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from utils.logger import TradingLogger
from abc import ABC, abstractmethod


class AlertChannel(ABC):
    """
    Abstract base class for alert channels.
    """

    @abstractmethod
    def send_alert(self, title, message, severity="INFO"):
        """
        Send an alert.
        
        Args:
            title: str - Alert title
            message: str - Alert message
            severity: str - Alert severity (INFO, WARNING, ERROR)
        """
        pass


class EmailAlert(AlertChannel):
    """
    Send alerts via email.
    """

    def __init__(self, sender_email, sender_password, recipient_email, smtp_server="smtp.gmail.com", smtp_port=587):
        """
        Initialize email alert channel.
        
        Args:
            sender_email: str - Sender email address
            sender_password: str - Email password or app password
            recipient_email: str or list - Recipient email(s)
            smtp_server: str - SMTP server address
            smtp_port: int - SMTP server port
        """
        self.sender_email = sender_email
        self.sender_password = sender_password
        self.recipient_email = recipient_email if isinstance(recipient_email, list) else [recipient_email]
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.logger = TradingLogger.get_logger()

    def send_alert(self, title, message, severity="INFO"):
        """
        Send email alert.
        
        Args:
            title: str - Alert title
            message: str - Alert message
            severity: str - Alert severity
        """
        try:
            # Color code by severity
            color_map = {
                "INFO": "#0066cc",
                "WARNING": "#ff9900",
                "ERROR": "#cc0000",
            }
            color = color_map.get(severity, "#0066cc")
            
            # Create HTML email
            html_content = f"""
            <html>
                <body style="font-family: Arial, sans-serif;">
                    <div style="border-left: 4px solid {color}; padding: 20px; background: #f5f5f5;">
                        <h2 style="color: {color}; margin-top: 0;">{severity}: {title}</h2>
                        <p>{message}</p>
                        <p style="color: #666; font-size: 12px;">
                            <strong>Timestamp:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                            <strong>System:</strong> Intraday Trading System
                        </p>
                    </div>
                </body>
            </html>
            """
            
            # Create email message
            email_message = MIMEMultipart("alternative")
            email_message["Subject"] = f"[{severity}] {title}"
            email_message["From"] = self.sender_email
            email_message["To"] = ", ".join(self.recipient_email)
            
            email_message.attach(MIMEText(html_content, "html"))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.sender_email, self.sender_password)
                server.sendmail(
                    self.sender_email,
                    self.recipient_email,
                    email_message.as_string()
                )
            
            self.logger.info(f"Email alert sent: {title}")
        
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {str(e)}")


class SMSAlert(AlertChannel):
    """
    Send alerts via SMS using Twilio.
    """

    def __init__(self, account_sid, auth_token, from_number, to_number):
        """
        Initialize SMS alert channel.
        
        Args:
            account_sid: str - Twilio account SID
            auth_token: str - Twilio authentication token
            from_number: str - From phone number
            to_number: str or list - To phone number(s)
        """
        try:
            from twilio.rest import Client
            self.client = Client(account_sid, auth_token)
        except ImportError:
            raise ImportError("twilio package required. Install with: pip install twilio")
        
        self.from_number = from_number
        self.to_number = to_number if isinstance(to_number, list) else [to_number]
        self.logger = TradingLogger.get_logger()

    def send_alert(self, title, message, severity="INFO"):
        """
        Send SMS alert.
        
        Args:
            title: str - Alert title
            message: str - Alert message
            severity: str - Alert severity
        """
        try:
            sms_message = f"[{severity}] {title}\n{message}"
            
            # Truncate to SMS length limit
            if len(sms_message) > 160:
                sms_message = sms_message[:157] + "..."
            
            for to_number in self.to_number:
                self.client.messages.create(
                    body=sms_message,
                    from_=self.from_number,
                    to=to_number
                )
            
            self.logger.info(f"SMS alert sent: {title}")
        
        except Exception as e:
            self.logger.error(f"Failed to send SMS alert: {str(e)}")


class AlertManager:
    """
    Centralized alert management system.
    """

    def __init__(self):
        """
        Initialize alert manager.
        """
        self.logger = TradingLogger.get_logger()
        self.channels = []  # List of alert channels

    def add_channel(self, channel):
        """
        Add an alert channel.
        
        Args:
            channel: AlertChannel - Alert channel instance
        """
        self.channels.append(channel)
        self.logger.info(f"Alert channel added: {channel.__class__.__name__}")

    def send_trade_entry_alert(self, symbol, direction, entry_price, stop_loss, target):
        """
        Send trade entry alert.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            entry_price: float - Entry price
            stop_loss: float - Stop loss price
            target: float - Target price
        """
        title = f"Trade Entry: {symbol} {direction}"
        message = f"""
Entry Price: ₹{entry_price:.2f}
Stop Loss: ₹{stop_loss:.2f}
Target: ₹{target:.2f}
Risk: ₹{abs(entry_price - stop_loss):.2f}
        """
        self.send_alert(title, message, "INFO")

    def send_trade_exit_alert(self, symbol, direction, exit_price, pnl, pnl_percent, reason):
        """
        Send trade exit alert.
        
        Args:
            symbol: str - Trading symbol
            direction: str - BUY or SELL
            exit_price: float - Exit price
            pnl: float - Profit/loss amount
            pnl_percent: float - Profit/loss percentage
            reason: str - Exit reason
        """
        severity = "INFO" if pnl >= 0 else "WARNING"
        title = f"Trade Exit: {symbol} {direction}"
        message = f"""
Exit Price: ₹{exit_price:.2f}
P&L: ₹{pnl:.2f} ({pnl_percent:.2f}%)
Reason: {reason}
        """
        self.send_alert(title, message, severity)

    def send_stop_loss_alert(self, symbol, stop_loss_price):
        """
        Send stop loss hit alert.
        
        Args:
            symbol: str - Trading symbol
            stop_loss_price: float - Stop loss price
        """
        title = f"Stop Loss Hit: {symbol}"
        message = f"Position stopped out at ₹{stop_loss_price:.2f}"
        self.send_alert(title, message, "WARNING")

    def send_target_alert(self, symbol, target_price):
        """
        Send profit target reached alert.
        
        Args:
            symbol: str - Trading symbol
            target_price: float - Target price
        """
        title = f"Profit Target Reached: {symbol}"
        message = f"Position exited at target ₹{target_price:.2f}"
        self.send_alert(title, message, "INFO")

    def send_risk_alert(self, message):
        """
        Send risk management alert.
        
        Args:
            message: str - Alert message
        """
        title = "Risk Alert"
        self.send_alert(title, message, "WARNING")

    def send_error_alert(self, error_message):
        """
        Send system error alert.
        
        Args:
            error_message: str - Error message
        """
        title = "System Error"
        self.send_alert(title, error_message, "ERROR")

    def send_alert(self, title, message, severity="INFO"):
        """
        Send alert through all configured channels.
        
        Args:
            title: str - Alert title
            message: str - Alert message
            severity: str - Alert severity
        """
        for channel in self.channels:
            try:
                channel.send_alert(title, message, severity)
            except Exception as e:
                self.logger.error(f"Error sending alert via {channel.__class__.__name__}: {str(e)}")
