"""
Lightweight signature/rule checks for MITM and Replay attacks.

We use rules here (not ML) because CIC-IDS2017 has no labeled examples
of these attack types, and both have simple, well-defined signatures
that don't need a statistical model - a duplicate/replayed command is
detected by comparing payload + timestamp, not by "learning" a pattern.

Your backend team should call these on live command/telemetry events,
in addition to calling the ML models on network flow features.

`event` example expected from the backend:
{
    "src_mac": "AA:BB:CC:00:11:22",
    "src_ip": "10.0.0.5",
    "payload_hash": "9f2b...",
    "timestamp": 1732521600.0,
    "sequence_number": 4821,
}
"""
from collections import defaultdict

# In-memory state (swap for Redis/DB in production for multi-instance backends)
_seen_mac_ip_pairs = defaultdict(set)     # ip -> set of macs ever seen for it
_seen_payload_hashes = {}                 # payload_hash -> last timestamp seen
_seen_sequence_numbers = defaultdict(set) # src_ip -> set of sequence numbers seen

REPLAY_WINDOW_SECONDS = 300  # a repeated payload within 5 min is suspicious


def check_mitm(event: dict) -> dict:
    """Flags if an IP suddenly maps to a MAC address it hasn't used before -
    classic sign of ARP spoofing / a MITM position change."""
    ip, mac = event.get("src_ip"), event.get("src_mac")
    if ip is None or mac is None:
        return {"is_mitm_suspect": False, "reason": None}

    known_macs = _seen_mac_ip_pairs[ip]
    is_suspect = len(known_macs) > 0 and mac not in known_macs
    known_macs.add(mac)

    return {
        "is_mitm_suspect": is_suspect,
        "reason": f"IP {ip} previously seen with different MAC(s)" if is_suspect else None,
    }


def check_replay(event: dict) -> dict:
    """Flags if the exact same payload hash reappears within the replay
    window, or if a sequence number that was already used shows up again."""
    payload_hash = event.get("payload_hash")
    ts = event.get("timestamp")
    src_ip = event.get("src_ip")
    seq = event.get("sequence_number")

    is_replay = False
    reason = None

    if payload_hash is not None and ts is not None:
        last_seen = _seen_payload_hashes.get(payload_hash)
        if last_seen is not None and (ts - last_seen) < REPLAY_WINDOW_SECONDS:
            is_replay = True
            reason = "Duplicate payload seen within replay window"
        _seen_payload_hashes[payload_hash] = ts

    if not is_replay and src_ip is not None and seq is not None:
        if seq in _seen_sequence_numbers[src_ip]:
            is_replay = True
            reason = "Duplicate sequence number reused"
        _seen_sequence_numbers[src_ip].add(seq)

    return {"is_replay_suspect": is_replay, "reason": reason}


def run_rule_checks(event: dict) -> dict:
    result = {}
    result.update(check_mitm(event))
    result.update(check_replay(event))
    return result
