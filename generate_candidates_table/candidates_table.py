import pickle
from collections import Counter
from datetime import datetime
import requests
import json

API_KEY = # https://www.livecoinwatch.com/tools/api#try
candidate_algorithms = None

privacy_cpu_coins = ['SFX', 'Sumokoin', 'Raptoreum', 'Monero', 'XMC', 'Zephyr', 'Verus']

asic_resistant_algorithms = ['kawpow', 'ethash', 'ghostrider', 'neoscrypt', 'randomx', 'equihash(192,7)', 'lyra2z',
                             'firopow', 'flex', 'cuckoocycle', 'equihash(210,9)', 'chukwa', 'x16rt', 'wildkeccak',
                             'bcd', 'beamhashiii', 'honeycomb', 'zhash', 'megabtx', 'cortex', 'astrobwtv2',
                             'dynexsolve', 'autolykos2', 'equihash(125,4)', 'yescryptr16', 'bmw512', 'equihash(144,5)',
                             'ironfish', 'chukwaixi', 'karlsenhash', 'meowpow', 'nexapow', 'progpowz', 'randomhash2',
                             'hmq1725', 'radiant', 'progpowsero', 'randomsfx', 'yespower', 'cryptonightr',
                             'cryptonighttalleo', 'yescrypt', 'lyra2rev2', 'argon2d', 'x16rv2', 'verushash', 'verthash',
                             'randomxdag', 'xelishash']

# https://www.awesomeminer.com/algorithm-list
awesomeminer_cpu_miners = [
    'CpuMiner-Opt', 'SRBMiner-Multi', 'NanoMiner', 'JCE CPU Miner', 'XMRig CPU Miner', 'RhMiner', 'XMR-Stak-RX'
]

# https://xmrig.com/docs/algorithms
xmrig_cpu_algorithms = [
    'GhostRider', 'RandomGRAFT', 'CryptoNight-Femto', 'Argon2id', 'Conceal', 'RandomKEVA',
    'CryptoNight-Pico', 'RandomSFX', 'RandomARQ', 'RandomX', 'Argon2id', 'Argon2id', 'RandomWOW',
    'CryptoNight variant 1 with half iterations',
    'CryptoNight variant 2 with 3/4 iterations and reversed shuffle operation',
    'CryptoNight variant 2 with 3/4 iterations', 'CryptoNight variant 2 with double iterations',
    'CryptoNightR', 'CryptoNight-Pico', 'CryptoNight variant 2 with half iterations',
    'CryptoNight variant 2', 'CryptoNight variant 0', 'CryptoNight variant 1', 'CryptoNight-Heavy',
    'CryptoNight-Heavy', 'CryptoNight-Heavy', 'CryptoNight variant 1', 'CryptoNight-Lite variant 1',
    'CryptoNight-Lite variant 0', 'CryptoNight'
]

# https://github.com/doktor83/SRBMiner-Multi/blob/master/Readme
SRBMiner_cpu_algorithms = [
    'argon2d_16000', 'argon2d_dynamic', 'argon2id_chukwa', 'argon2id_chukwa2', 'aurum',
    'cpupower', 'cryptonight_ccx', 'cryptonight_gpu', 'cryptonight_turtle', 'cryptonight_upx',
    'cryptonight_xhv', 'curvehash', 'flex', 'ghostrider', 'lyra2v2_webchain', 'mike',
    'minotaurx', 'panthera', 'pufferfish2bmb', 'randomarq', 'randomepic', 'randomgrft',
    'randomkeva', 'randomnevo', 'randomscash', 'randomsfx', 'randomtuske', 'randomx',
    'randomxeq', 'randomyada', 'verushash', 'xelishash', 'xelishashv2', 'xelishashv2_pepew',
    'yescrypt', 'yescryptr16', 'yescryptr32', 'yescryptr8', 'yespower', 'yespower2b',
    'yespoweric', 'yespowerltncg', 'yespowermgpc', 'yespowerr16', 'yespowersugar',
    'yespowertide', 'yespowerurx'
]

# https://github.com/JayDDee/cpuminer-opt/wiki/Supported--Algorithms
cpuminer_cpu_algorithms = [
    'allium', 'anime', 'argon2', 'argon2d250', 'argon2d500', 'argon2d4096', 'axiom', 'blake',
    'blake2b', 'blake2s', 'blakecoin', 'bmw', 'bmw512', 'c11', 'decred', 'deep', 'dmd-gr',
    'groestl', 'hex', 'hmq1725', 'jha', 'keccak', 'keccakc', 'lbry', 'luffa', 'lyra2h',
    'lyra2re', 'lyra2rev2', 'lyra2rev3', 'lyra2z', 'lyra2z330', 'm7m', 'minotaur', 'minotaurx',
    'myr-gr', 'neoscrypt', 'nist5', 'pentablake', 'phi1612', 'phi2', 'pluck', 'polytimos',
    'power2b', 'quark', 'qubit', 'scrypt', 'scrypt:N', 'scryptn2', 'sha256d', 'sha256dt',
    'sha256q', 'sha256t', 'sha3d', 'sha512256d', 'shavite3', 'skein', 'skein2', 'skunk',
    'sonoa', 'timetravel', 'timetravel10', 'tribus', 'vanilla', 'veltor', 'verthash',
    'whirlpool', 'whirlpoolx', 'x11', 'x11evo', 'x11gost', 'x12', 'x13', 'x13bcd', 'x13sm3',
    'x14', 'x15', 'x16r', 'x16rv2', 'x16rt', 'x16rt-veil', 'x16s', 'x17', 'x20r', 'x21s',
    'x22i', 'x25x', 'xevan', 'yescrypt', 'yescryptr8', 'yescryptr8g', 'yescryptr16', 'yescryptr32',
    'yespower', 'yespowerr16', 'yespower-b2b', 'zr5'
]

# https://github.com/nanopool/nanominer
nanominer_cpu_algorithms = ['RandomX', 'RandomNevo', 'Verushash']
rhminer_cpu_algorithms = ['RandomHash2']

# Combine all CPU algorithms from different mining applications
cpu_algorithms = Counter(
    [algo.lower() for algo in nanominer_cpu_algorithms + cpuminer_cpu_algorithms +
     SRBMiner_cpu_algorithms + xmrig_cpu_algorithms + rhminer_cpu_algorithms]
)

def filter_candidate_algorithms():
    """Filter candidate algorithms (from minerstat) that are CPU-minable"""
    response = requests.get(url="https://api.minerstat.com/v2/coins")
    data = response.json()
    minestat_algorithms_data = Counter([x['algorithm'] for x in data if x['network_hashrate'] > 0])
    minestat_algorithms = [k for k, v in minestat_algorithms_data.items()]
    return [algo for algo in minestat_algorithms if algo.lower() in cpu_algorithms]


def get_asic_candidates_coins():
    """Get active coins that match candidate CPU-minable algorithms."""
    response = requests.get(
        url="https://api.minerstat.com/v2/coins",
        params={'algo': ','.join(candidate_algorithms)}
    )
    data = response.json()
    active_coins = [x for x in data if x['network_hashrate'] > 0]
    return active_coins


def get_coin_metadata(coin_code):
    """Retrieve coin metadata synchronously from livecoinwatch."""
    url = "https://api.livecoinwatch.com/coins/single"
    payload = json.dumps({"currency": "USD", "code": coin_code, "meta": True})
    headers = {
        'content-type': 'application/json',
        'x-api-key': API_KEY
    }

    response = requests.post(url, headers=headers, data=payload)
    if response.status_code == 200:
        print('.', end='')
        return response.json()
    else:
        return None


def load_candidates(file_path='data.cpu_algorithms.pkl'):
    """Load candidate coin data from file if it exists."""
    try:
        with open(file_path, 'rb') as f:
            return pickle.load(f)
    except FileNotFoundError:
        return None


def save_candidates(candidates, file_path='data.cpu_algorithms.pkl'):
    """Save candidate coin data to file."""
    with open(file_path, 'wb') as f:
        pickle.dump(candidates, f)


def calculate_profit(candidates):
    """Calculate KHR profit for each candidate."""
    for coin in candidates:
        price = coin['meta']['rate'] if coin['meta'] and coin['meta'].get('rate') else coin['price']
        coin.update({'khr_profit': (1000 / coin['network_hashrate']) * coin['reward_block'] * price})
        coin['updated'] = datetime.fromtimestamp(coin['updated'])
    return candidates


def filter_final_candidates(candidates):
    """Filter final candidate list to those with metadata and categories."""
    return [c for c in candidates if c['meta'] and 'categories' in c['meta']]


def print_table(coins):
    """Print the final coins in a formatted table."""
    # Determine max column widths for formatting
    name_width = max(len(c['name']) for c in coins) if coins else 10
    algo_width = max(len(c['algorithm']) for c in coins) if coins else 10

    header = f"{'Name'.ljust(name_width)} | {'Algorithm'.ljust(algo_width)} | Privacy Coin | ASIC resistant | KHR Profit"
    print(header)
    print('-' * len(header))

    for c in coins:
        privacy = 'Yes' if ('categories' in c['meta'] and 'privacy_coins' in c['meta']['categories']) else 'No'
        asic_resistant = 'Yes' if c['algorithm'].lower() in asic_resistant_algorithms else 'No'
        print(
            f"{c['name'].ljust(name_width)} | "
            f"{c['algorithm'].ljust(algo_width)} | "
            f"{privacy.center(12)} | "
            f"{asic_resistant.center(14)} | "
            f"{c['khr_profit']:.8f}"
        )


def print_privacy_coin_exchanges(final_coins):
    """Print exchanges and markets for known privacy CPU coins."""
    for coin_name in privacy_cpu_coins:
        candidate = next(
            (x for x in final_coins if x['name'] == coin_name or
             (x['meta'] and x['meta'].get('name') == coin_name)), None
        )
        if candidate and candidate['meta']:
            print(
                f"{coin_name} - exchanges: {candidate['meta']['exchanges']} - markets: {candidate['meta']['markets']}")


if __name__ == '__main__':
    candidates = load_candidates()

    # If no cached data, fetch fresh data and compute profits
    if candidates is None:
        candidate_algorithms = filter_candidate_algorithms()
        candidates = get_asic_candidates_coins()

        for coin in candidates:
            meta = get_coin_metadata(coin['coin'])
            coin.update({'meta': meta})
        print('done')

        candidates = calculate_profit(candidates)
        candidates = sorted(candidates, key=lambda x: x['khr_profit'], reverse=True)
        save_candidates(candidates)

    # Filter and print final results
    final = filter_final_candidates(candidates)
    print_table(final)
    print_privacy_coin_exchanges(final)
