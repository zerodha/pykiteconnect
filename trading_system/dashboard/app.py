# -*- coding: utf-8 -*-
"""
Web Dashboard
Flask-based web UI for real-time monitoring
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
from datetime import datetime
import json

app = Flask(__name__)
CORS(app)

# Global engine reference (set by main.py)
engine = None


@app.route("/")
def index():
    """Main dashboard page."""
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """Get engine status."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    status = engine.get_status()
    return jsonify(status)


@app.route("/api/positions")
def api_positions():
    """Get all open positions."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    positions = engine.position_tracker.get_all_positions()
    positions_list = []
    
    for symbol, pos in positions.items():
        positions_list.append({
            "symbol": pos["symbol"],
            "side": pos["side"],
            "quantity": pos["quantity"],
            "entry_price": pos["entry_price"],
            "current_pnl": pos["pnl"],
            "pnl_percent": pos["pnl_percent"],
            "stop_loss": pos["stop_loss"],
            "target": pos["target"],
            "entry_time": pos["entry_time"].isoformat() if pos["entry_time"] else None,
        })
    
    return jsonify({"positions": positions_list})


@app.route("/api/signals")
def api_signals():
    """Get current signals."""
    if not engine or not engine.strategy:
        return jsonify({"error": "Engine not initialized"}), 500
    
    signals = {}
    for symbol, signal in engine.strategy.signals.items():
        signals[symbol] = {
            "direction": signal.get("direction"),
            "confidence": signal.get("confidence"),
            "strength": signal.get("strength"),
            "reason": signal.get("reason"),
            "timestamp": signal.get("timestamp").isoformat() if signal.get("timestamp") else None,
            "indicators": signal.get("indicators", {}),
        }
    
    return jsonify(signals)


@app.route("/api/risk")
def api_risk():
    """Get risk management summary."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    risk_summary = engine.risk_manager.get_risk_summary()
    return jsonify(risk_summary)


@app.route("/api/trades")
def api_trades():
    """Get closed trades history."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    trades = []
    for pos in engine.position_tracker.closed_positions:
        trades.append({
            "symbol": pos["symbol"],
            "side": pos["side"],
            "quantity": pos["quantity"],
            "entry_price": pos["entry_price"],
            "exit_price": pos["exit_price"],
            "pnl": pos["pnl"],
            "pnl_percent": pos["pnl_percent"],
            "entry_time": pos["entry_time"].isoformat() if pos["entry_time"] else None,
            "exit_time": pos["exit_time"].isoformat() if pos["exit_time"] else None,
        })
    
    return jsonify({"trades": trades})


@app.route("/api/start", methods=["POST"])
def api_start():
    """Start trading engine."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    try:
        result = engine.start(threaded=True)
        return jsonify({"success": result, "message": "Engine started" if result else "Engine start failed"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/stop", methods=["POST"])
def api_stop():
    """Stop trading engine."""
    if not engine:
        return jsonify({"error": "Engine not initialized"}), 500
    
    try:
        engine.stop()
        return jsonify({"success": True, "message": "Engine stopped"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/health")
def api_health():
    """Health check."""
    return jsonify({"status": "healthy", "timestamp": datetime.now().isoformat()})


if __name__ == "__main__":
    app.run(debug=True, port=5000)
