import json

OptimisticOracleV2 = "0xeE3Afe347D5C74317041E2618C49534dAf887c24"
UmaCtfAdapter = "0x6A9D222616C90FcA5754cd1333cFD9b7fb6a4F74"
yesOrNoIdentifier = "0x5945535f4f525f4e4f5f51554552590000000000000000000000000000000000"

def load_abi(filename):
    with open(f"./abi/{filename}") as f:
        return json.load(f)