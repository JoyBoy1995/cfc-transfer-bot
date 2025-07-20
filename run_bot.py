#!/usr/bin/env python3
"""
Transfer Bot Entry Point
"""

import asyncio
import logging
from bot.main import TransferBot

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def main():
    """Main entry point"""
    bot = TransferBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())