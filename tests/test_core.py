import unittest
from examples.core import (Event, cue_cap, plan_cues, resolve_identity, compile_music,
                           group_sources, reserve_once, may_submit, rank_excerpts)


class PlanningTests(unittest.TestCase):
    def test_duration_cap_is_strict(self):
        self.assertEqual([cue_cap(t) for t in (30000, 40000, 45000, 60000, 180000)], [2, 3, 4, 5, 12])

    def test_invalid_duration(self):
        for value in (29999, 180001, True, 45000.0):
            with self.assertRaises(ValueError): cue_cap(value)

    def test_no_events_means_one(self):
        self.assertEqual(plan_cues(45000, []), ((0, 45000),))

    def test_camera_emotion_do_not_split(self):
        events = [Event(t, kind, True, True) for t, kind in [(9000, "camera_cut"), (24000, "emotion_change")]]
        self.assertEqual(plan_cues(45000, events), ((0, 45000),))

    def test_six_second_reset_retained(self):
        self.assertEqual(plan_cues(45000, [Event(39000, "relationship_reset", True, True)]), ((0, 39000), (39000, 45000)))

    def test_unbound_or_transient_reset_merges(self):
        self.assertEqual(plan_cues(45000, [Event(15000, "scene_reset", False, True), Event(30000, "scene_reset", True, False)]), ((0, 45000),))

    def test_too_short_automatic_tail_suppressed(self):
        self.assertEqual(plan_cues(45000, [Event(41000, "scene_reset", True, True)]), ((0, 45000),))

    def test_creator_overrides_model(self):
        events = [Event(39000, "relationship_reset", True, True)]
        self.assertEqual(plan_cues(45000, events, []), ((0, 45000),))
        self.assertEqual(plan_cues(45000, events, [20000]), ((0, 20000), (20000, 45000)))

    def test_user_invalid_boundary(self):
        for points in ([1000], [41000], [20000, 20000], [10000, 14000], [-5000], [46000]):
            with self.assertRaises(ValueError): plan_cues(45000, [], points)

    def test_density_is_not_quota(self):
        events = [Event(t, "scene_reset", True, True) for t in range(5000, 45000, 5000)]
        windows = plan_cues(45000, events)
        self.assertEqual(len(windows), 4)
        self.assertTrue(all(b-a >= 5000 for a, b in windows))
        self.assertEqual(windows[0][0], 0)
        self.assertEqual(windows[-1][1], 45000)

    def test_too_many_user_cues_rejected(self):
        with self.assertRaisesRegex(ValueError, "cue_count"): plan_cues(45000, [], [10000, 20000, 30000, 35000])


class MusicTests(unittest.TestCase):
    def setUp(self): self.identity = {"setting": "palace", "palette": "electronic"}

    def test_identity_inherits_without_mutation(self):
        resolved, trace = resolve_identity(self.identity, [])
        self.assertEqual(resolved["setting"], "palace")
        resolved["setting"] = "studio"
        self.assertEqual(self.identity["setting"], "palace")
        self.assertEqual(trace["setting"], "episode")

    def test_local_override_requires_reason(self):
        with self.assertRaises(ValueError): resolve_identity(self.identity, [{"scope":"cue", "values":{"palette":"strings"}}])

    def test_override_scope_traced(self):
        result, trace = resolve_identity(self.identity, [{"scope":"cue", "reason":"new narrative role", "values":{"palette":"strings"}}])
        self.assertEqual(result, {"setting":"palace", "palette":"strings"})
        self.assertEqual(trace["palette"], "cue")

    def test_hook_overrides_atmosphere_proposal(self):
        result = compile_music(self.identity, carrier="atmosphere", energy="medium", first=True, character_presence="present")
        self.assertEqual((result["provider"], result["entry"]), ("mureka", "mature_rhythm"))
        self.assertIn("palace", result["prompt"])
        self.assertNotIn("second zero", result["prompt"])

    def test_unknown_opening_conservative_default(self):
        self.assertEqual(compile_music(self.identity, carrier="atmosphere", energy="low", first=True)["entry"], "mature_rhythm")

    def test_scene_only_allows_atmosphere(self):
        self.assertEqual(compile_music(self.identity, carrier="atmosphere", energy="low", first=True, character_presence="absent")["provider"], "stable_audio")

    def test_instrumental_is_enforced(self):
        result = compile_music(self.identity, carrier="motif", energy="low", first=False)
        self.assertEqual(result["voice"], "instrumental")
        self.assertIn("no singing, humming", result["prompt"])

    def test_recipe_reuse_is_exact(self):
        recipes = [{"cue_id":str(i),"provider":"mureka","prompt":"same","entry":"mature_rhythm"} for i in range(2)]
        self.assertEqual(len(group_sources(recipes)), 1)
        recipes[1]["prompt"] = "different"
        self.assertEqual(len(group_sources(recipes)), 2)

    def test_reset_cannot_share(self):
        self.assertEqual(len(group_sources([{"cue_id":"a","prompt":"same"},{"cue_id":"b","prompt":"same","reset":True}])), 2)


class CostAndSelectionTests(unittest.TestCase):
    def test_double_click_no_extra_charge(self):
        ledger = {}
        self.assertTrue(reserve_once(ledger,"source-a",2,5)["created"])
        self.assertFalse(reserve_once(ledger,"source-a",2,5)["created"])
        self.assertEqual(len(ledger),1)

    def test_budget_failure_does_not_mutate(self):
        ledger = {}
        with self.assertRaises(ValueError): reserve_once(ledger,"source",6,5)
        self.assertEqual(ledger,{})

    def test_conflicting_replay_rejected(self):
        ledger = {}; reserve_once(ledger,"source",2,5)
        with self.assertRaises(ValueError): reserve_once(ledger,"source",3,5)

    def test_unknown_is_not_safe_to_resubmit(self):
        self.assertTrue(may_submit("reserved"))
        for state in ("submission_unknown", "succeeded", "running", "failed"):
            self.assertFalse(may_submit(state))

    def test_excerpt_bounds_coverage_and_stability(self):
        base = dict(coverage=1, rhythm=.8, stability=.8, exit_softness=.8)
        windows = [{**base,"start_ms":40000}, {**base,"start_ms":10000}, {**base,"start_ms":20000,"coverage":.5}]
        self.assertEqual([w["start_ms"] for w in rank_excerpts(windows,15000,45000)], [10000])

    def test_excerpt_ties_deterministic(self):
        base = dict(coverage=1, rhythm=.8, stability=.8, exit_softness=.8)
        self.assertEqual([w["start_ms"] for w in rank_excerpts([{**base,"start_ms":20000},{**base,"start_ms":10000}],5000,45000)], [10000,20000])


if __name__ == "__main__": unittest.main()
