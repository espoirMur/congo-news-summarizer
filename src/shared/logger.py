import logging
import logging.handlers
import sys


class CustomFormatter(logging.Formatter):
	"""Custom formatter with colors for console output"""

	grey = "\x1b[38;20m"
	yellow = "\x1b[33;20m"
	red = "\x1b[31;20m"
	bold_red = "\x1b[31;1m"
	reset = "\x1b[0m"
	green = "\x1b[32m"

	# Format string with colors
	FORMATS = {
		logging.DEBUG: grey
		+ "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
		+ reset,
		logging.INFO: green
		+ "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
		+ reset,
		logging.WARNING: yellow
		+ "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
		+ reset,
		logging.ERROR: red
		+ "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
		+ reset,
		logging.CRITICAL: bold_red
		+ "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
		+ reset,
	}

	def format(self, record):
		log_fmt = self.FORMATS.get(record.levelno)
		formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
		return formatter.format(record)


def setup_logger(name="app"):
	"""
	Set up a logger with console and file handlers

	Args:
	    name (str): Logger name

	Returns:
	    logging.Logger: Configured logger instance
	"""
	logger = logging.getLogger(name)
	logger.setLevel(logging.DEBUG)
	if logger.handlers:
		return logger
	console_handler = logging.StreamHandler(sys.stdout)
	console_handler.setLevel(logging.DEBUG)
	console_handler.setFormatter(CustomFormatter())
	logger.addHandler(console_handler)

	return logger
