# -*- coding: utf-8 -*-
"""
Historical Data Fetcher
Integrate real historical data from Kite Connect
"""

from datetime import datetime, timedelta
import pandas as pd
from utils.logger import TradingLogger


class HistoricalDataFetcher:
    """
    Fetch historical OHLC data from Kite Connect API.
    """
    CANDLES_PER_DAY = {
        "1minute": 375,   # ~6.25 trading hours * 60 minutes
        "5minute": 75,    # ~375 / 5
        "15minute": 25,   # ~375 / 15
        "60minute": 6,    # ~375 / 60
    }

    def __init__(self, kite_instance):
        """
        Initialize data fetcher.
        
        Args:
            kite_instance: KiteConnect instance
        """
        self.kite = kite_instance
        self.logger = TradingLogger.get_logger()

    def fetch_instrument_token(self, exchange, symbol):
        """
        Get instrument token for a symbol.
        
        Args:
            exchange: str - NSE, BSE, NFO, MCX, etc.
            symbol: str - Trading symbol
            
        Returns:
            int - Instrument token or None
        """
        try:
            instruments = self.kite.instruments(exchange=exchange)
            for inst in instruments:
                if inst["tradingsymbol"] == symbol:
                    return inst["instrument_token"]
            self.logger.warning(f"Symbol {symbol} not found on {exchange}")
            return None
        except Exception as e:
            self.logger.error(f"Error fetching instrument token: {str(e)}")
            return None

    def fetch_historical_data(
        self,
        exchange,
        symbol,
        from_date,
        to_date,
        interval="5minute",
    ):
        """
        Fetch historical OHLC data.
        
        Args:
            exchange: str - NSE, MCX, etc.
            symbol: str - Trading symbol
            from_date: datetime - Start date
            to_date: datetime - End date
            interval: str - 1minute, 5minute, 15minute, 30minute, 60minute, daily
            
        Returns:
            list - OHLC data [{timestamp, open, high, low, close, volume}, ...]
        """
        try:
            # Get instrument token
            token = self.fetch_instrument_token(exchange, symbol)
            if not token:
                return None
            
            self.logger.info(
                f"Fetching {interval} data for {symbol} from {from_date.date()} to {to_date.date()}"
            )
            
            # Fetch historical data
            data = self.kite.historical_data(
                instrument_token=token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
            )
            
            self.logger.info(f"Fetched {len(data)} candles for {symbol}")
            return data
        
        except Exception as e:
            self.logger.error(f"Error fetching historical data for {symbol}: {str(e)}")
            return None

    def fetch_historical_data_by_token(
        self,
        instrument_token,
        from_date,
        to_date,
        interval="5minute",
    ):
        """
        Fetch historical OHLC data directly by instrument token.

        Args:
            instrument_token: int - Kite instrument token
            from_date: datetime - Start date
            to_date: datetime - End date
            interval: str - Candle interval

        Returns:
            list - OHLC data [{timestamp, open, high, low, close, volume}, ...]
        """
        try:
            if not instrument_token:
                return None

            data = self.kite.historical_data(
                instrument_token=instrument_token,
                from_date=from_date,
                to_date=to_date,
                interval=interval,
            )
            return data
        except Exception as e:
            self.logger.error(f"Error fetching historical data for token {instrument_token}: {str(e)}")
            return None

    def fetch_multiple_symbols(
        self,
        exchange,
        symbols,
        from_date,
        to_date,
        interval="5minute",
    ):
        """
        Fetch historical data for multiple symbols.
        
        Args:
            exchange: str - NSE, MCX, etc.
            symbols: list - Trading symbols
            from_date: datetime - Start date
            to_date: datetime - End date
            interval: str - Candle interval
            
        Returns:
            dict - {symbol: OHLC data}
        """
        data = {}
        for symbol in symbols:
            symbol_data = self.fetch_historical_data(
                exchange, symbol, from_date, to_date, interval
            )
            if symbol_data:
                data[symbol] = symbol_data
        
        self.logger.info(f"Fetched data for {len(data)}/{len(symbols)} symbols")
        return data

    def dataframe_from_historical(self, historical_data):
        """
        Convert historical data to pandas DataFrame.
        
        Args:
            historical_data: list - OHLC data from API
            
        Returns:
            pd.DataFrame - Historical data as DataFrame
        """
        if not historical_data:
            return None
        
        df = pd.DataFrame(historical_data)
        df["date"] = pd.to_datetime(df["date"])
        return df

    def get_last_n_candles(self, exchange, symbol, n=50, interval="5minute"):
        """
        Get last N candles for a symbol.
        
        Args:
            exchange: str - NSE, MCX, etc.
            symbol: str - Trading symbol
            n: int - Number of candles
            interval: str - Candle interval
            
        Returns:
            list - Last N candles
        """
        # Calculate date range based on interval
        if interval in self.CANDLES_PER_DAY:
            days_back = n // self.CANDLES_PER_DAY[interval] + 1
        else:  # daily
            days_back = n + 1
        
        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)
        
        data = self.fetch_historical_data(exchange, symbol, from_date, to_date, interval)
        
        if data and len(data) > n:
            return data[-n:]
        return data

    def get_last_n_candles_by_token(self, instrument_token, n=50, interval="5minute"):
        """
        Get last N candles for an instrument token.

        Args:
            instrument_token: int - Instrument token
            n: int - Number of candles
            interval: str - Candle interval

        Returns:
            list - Last N candles
        """
        if interval in self.CANDLES_PER_DAY:
            days_back = n // self.CANDLES_PER_DAY[interval] + 1
        else:
            days_back = n + 1

        to_date = datetime.now()
        from_date = to_date - timedelta(days=days_back)

        data = self.fetch_historical_data_by_token(
            instrument_token=instrument_token,
            from_date=from_date,
            to_date=to_date,
            interval=interval,
        )

        if data and len(data) > n:
            return data[-n:]
        return data
