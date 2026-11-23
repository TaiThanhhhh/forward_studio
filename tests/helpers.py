"""Tiện ích chung cho test."""
import copy
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
FIXTURES = os.path.join(HERE, "fixtures")
SNAPSHOTS = os.path.join(HERE, "snapshots")


def demo_raw():
    with open(os.path.join(FIXTURES, "storyboard_demo.json"), encoding="utf-8") as f:
        return json.load(f)


def demo():
    from vidlib import storyboard
    return storyboard.normalize(demo_raw())


def mini(**shot_over):
    """Storyboard tối thiểu 1 shot, ghi đè trường shot."""
    from vidlib import storyboard
    s = {
        "id": "C01", "beat": "hook", "target_sec": 1.4,
        "subject": "the white ball", "camera": "Locked-off static shot",
        "start_frame": {"desc": "A white ball resting on a white line, centered"},
        "action": [{"t": [0, 2], "do": "The white ball bounces high with squash-and-stretch and lands hard"}],
    }
    s.update(shot_over)
    return storyboard.normalize({"topic": "test", "shots": [s], "ingredients": [
        {"id": "REF_A", "desc": "a white ball"}, {"id": "REF_B", "desc": "a white cube"}]})


def snapshot(name, data, test):
    """So sánh với tests/snapshots/<name>.json; UPDATE_SNAPSHOTS=1 để ghi lại."""
    path = os.path.join(SNAPSHOTS, name + ".json")
    text = json.dumps(data, ensure_ascii=False, indent=2) + "\n"
    if os.environ.get("UPDATE_SNAPSHOTS") or not os.path.exists(path):
        os.makedirs(SNAPSHOTS, exist_ok=True)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        return
    with open(path, encoding="utf-8") as f:
        want = f.read()
    test.maxDiff = None
    test.assertEqual(json.loads(want), json.loads(text), f"Snapshot {name} lệch — chạy lại với UPDATE_SNAPSHOTS=1 "
                                                          f"nếu thay đổi là chủ ý.")


def deep(x):
    return copy.deepcopy(x)
