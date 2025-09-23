import json
import os
from timeline_analyzer import TimelineAnalyzer, SoloKillEvent


def make_simple_timeline():
    # 単純な timeline: 1フレームに1つのキルイベント（アシストなし）と participantFrames
    return {
        "info": {
            "frames": [
                {
                    "timestamp": 60000,
                    "participantFrames": {
                        "1": {"level": 2, "currentGold": 300, "totalGold": 500, "xp": 300, "minionsKilled": 10, "jungleMinionsKilled": 0, "position": {"x": 1000, "y": 2000}},
                        "2": {"level": 1, "currentGold": 50, "totalGold": 200, "xp": 100, "minionsKilled": 2, "jungleMinionsKilled": 0, "position": {"x": 1100, "y": 2100}}
                    },
                    "events": [
                        {"type": "CHAMPION_KILL", "killerId": 1, "victimId": 2, "timestamp": 60000, "assistingParticipantIds": [], "shutdownBounty": 0, "bounty": 0}
                    ]
                }
            ]
        }
    }


def make_simple_match():
    return {
        "metadata": {"matchId": "TESTMATCH1"},
        "info": {"gameDuration": 1200, "participants": [
            {"participantId": 1, "puuid": "p1", "championId": 11, "championName": "TestChamp1", "teamId": 100, "lane": "TOP", "teamPosition": "TOP", "win": False},
            {"participantId": 2, "puuid": "p2", "championId": 22, "championName": "TestChamp2", "teamId": 200, "lane": "TOP", "teamPosition": "TOP", "win": True}
        ]}
    }


def test_simple_solo_kill_detection(tmp_path):
    ta = TimelineAnalyzer()
    timeline = make_simple_timeline()
    match = make_simple_match()

    result = ta.analyze_timeline(timeline, match)

    assert isinstance(result, dict)
    assert result.get('match_id') == 'TESTMATCH1'
    assert 'solo_kills' in result
    assert len(result['solo_kills']) == 1

    # ファイル保存・読み込みテスト
    p = tmp_path / "solo_kills.json"
    assert ta.save_solo_kills_to_file(result['solo_kills'], str(p))
    loaded = ta.load_solo_kills_from_file(str(p))
    assert len(loaded) == 1
    assert isinstance(loaded[0], SoloKillEvent)
