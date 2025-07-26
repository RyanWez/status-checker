#!/usr/bin/env python3
"""
Test script for Myanmar timezone functionality
"""
import asyncio
import logging
from datetime import datetime, timezone, timedelta
from utils.timezone import myanmar_now, format_myanmar_time, format_myanmar_time_short, format_myanmar_date, to_myanmar_time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_timezone():
    """Test Myanmar timezone functions"""
    try:
        logger.info("Testing Myanmar Timezone Functions...")
        
        # Test current time
        utc_now = datetime.now(timezone.utc)
        myanmar_time = myanmar_now()
        
        logger.info(f"UTC Time: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        logger.info(f"Myanmar Time: {myanmar_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Calculate time difference
        time_diff = myanmar_time - utc_now.replace(tzinfo=None)
        expected_diff = timedelta(hours=6, minutes=30)
        
        logger.info(f"Time difference: {time_diff}")
        logger.info(f"Expected difference: {expected_diff}")
        
        # Test formatting functions
        test_datetime = datetime(2024, 1, 20, 15, 30, 45, tzinfo=timezone.utc)
        
        logger.info("\n=== Formatting Tests ===")
        logger.info(f"Original UTC: {test_datetime}")
        logger.info(f"Myanmar full: {format_myanmar_time(test_datetime)}")
        logger.info(f"Myanmar short: {format_myanmar_time_short(test_datetime)}")
        logger.info(f"Myanmar date: {format_myanmar_date(test_datetime)}")
        
        # Test conversion
        myanmar_converted = to_myanmar_time(test_datetime)
        logger.info(f"Converted to Myanmar: {myanmar_converted}")
        
        # Test with naive datetime (should assume UTC)
        naive_datetime = datetime(2024, 1, 20, 15, 30, 45)
        myanmar_from_naive = to_myanmar_time(naive_datetime)
        logger.info(f"Naive datetime: {naive_datetime}")
        logger.info(f"Converted from naive: {myanmar_from_naive}")
        
        # Verify the time difference is correct (6:30 ahead of UTC)
        utc_test = datetime(2024, 1, 20, 15, 30, 45, tzinfo=timezone.utc)
        myanmar_test = to_myanmar_time(utc_test)
        expected_myanmar = datetime(2024, 1, 20, 22, 0, 45)  # 15:30 + 6:30 = 22:00
        
        logger.info(f"\n=== Verification ===")
        logger.info(f"UTC: 15:30:45")
        logger.info(f"Myanmar: {myanmar_test.strftime('%H:%M:%S')}")
        logger.info(f"Expected: 22:00:45")
        
        if myanmar_test.hour == 22 and myanmar_test.minute == 0:
            logger.info("✅ Timezone conversion is correct!")
        else:
            logger.error("❌ Timezone conversion is incorrect!")
        
        # Test current time display
        logger.info(f"\n=== Current Time Display ===")
        logger.info(f"Current Myanmar time: {format_myanmar_time_short(myanmar_now())}")
        logger.info(f"Current Myanmar date: {format_myanmar_date(myanmar_now())}")
        
        logger.info("\n✅ Timezone test completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

if __name__ == "__main__":
    test_timezone()