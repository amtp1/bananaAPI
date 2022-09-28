from os import path, mkdir
import argparse

from logger.logger import logger
from utils.utils import *
from exceptions.exceptions import *

BDATA_PATH = r"bdata"
DEBUG_PATH = r"debug"

def str2bool(v):
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')

def main():
    # Check bdata folder.
    if not path.exists(BDATA_PATH):
        mkdir(BDATA_PATH) # Create bdata folder.
    # Check debug folder.
    elif not path.exists(DEBUG_PATH):
        mkdir(DEBUG_PATH) # Create debug folder.

    parser = argparse.ArgumentParser(description="BBC (Base Banana Commands)") # Init Argument Parser object
    parser.add_argument('-current_balance', action='store_true', help='Show current balance of account') # Set argument for run base func
    parser.add_argument('-trades', type=str, default=None, help='Show trades of account. Example: python main.py -trades=USDTRUB') # Set argument for run base func
    parser.add_argument('-to_excel', type=str2bool, default=False, help='Save trades to excel file') # Save trades to excel file
    parser.add_argument('-run', action='store_true', help="Run stream") # Run stream (main function)
    parser.add_argument('-iter', type=int, default=0, help="Count iterations") # Count iterations
    parser.add_argument('-upload_all_couples', action='store_true', help='Upload all couples to excel by limit')
    parser.add_argument('-limit', type=int, default=1, help="Limit price of couple") # Limit price of couple

    args = parser.parse_args() # Parse arguments
    if not any(args.__dict__.values()):
        parser.print_help() # Show help message
    else:
        core = Core() # Init Core object
        if args.current_balance:
            current_balance = core.current_balance() # Get current balance
            logger.info("Current balance: {:.2f}$".format(current_balance)) # Show current balance
        elif args.trades:
            core.trades(symbol=args.trades, to_excel=args.to_excel)
        elif args.run:
            if args.iter <= 0:
                return logger.info("Wrong value. Must not be less than or equal to zero.")
            else:
                core.stream(count_iter=args.iter)
        elif args.upload_all_couples:
            if args.limit <= 0:
                return logger.info("Wrong value. Must not be less than or equal to zero.")
            else:
                core.upload_all_couples(args.limit)

if __name__ == "__main__":
    try:
        main() # Call main function
    except KeyboardInterrupt:
        logger.info("Program stopped.")