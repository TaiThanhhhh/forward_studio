"""Vòng 15 — Platform-Specific YouTube Shorts & TikTok SEO tests."""
import os
import tempfile
import unittest

from vidlib import qareport


class Round15PlatformSeoTests(unittest.TestCase):
    def test_legacy_publish_strips_shorts_from_tiktok_and_reels(self):
        sb = {
            "title": "Why AI Can't Count R's in Strawberry",
            "caption": "AI never sees letters—only token numbers.",
            "publish": {
                "titles": [
                    "Why AI Can't Count the R's in 'Strawberry'",
                    "The Real Reason AI Thinks Strawberry Has 2 R's",
                    "AI Never Sees Letters — Here's What It Sees",
                ],
                "description": "AI chops words into token IDs for speed. Source: OpenAI tiktoken — True.",
                "hashtags": ["ai", "chatgpt", "strawberry", "tech", "shorts"],
            },
        }
        seo = qareport.platform_seo(sb)
        self.assertNotIn("shorts", [t.lower() for t in seo["tiktok"]["hashtags"]])
        self.assertNotIn("shorts", [t.lower() for t in seo["instagram_reels"]["hashtags"]])
        self.assertLessEqual(len(seo["youtube_shorts"]["hashtags"]), 3)
        self.assertEqual(seo["tiktok"]["caption"], sb["caption"])

    def test_split_publish_passes_with_zero_warnings_and_writes_sections(self):
        sb = {
            "title": "Why AI Can't Count the R's in 'Strawberry'",
            "publish": {
                "youtube_shorts": {
                    "titles": [
                        "Why AI Can't Count the R's in 'Strawberry'",
                        "How ChatGPT Sees 'Strawberry' (496, 675, 15717)",
                        "Why LLMs Fail Simple Spelling Tests",
                    ],
                    "description": (
                        "Ask an AI how many R's are in strawberry and it often says two. "
                        "That happens because large language models read numeric token IDs instead of individual letters. "
                        "Source: OpenAI tiktoken cl100k_base — True."
                    ),
                    "hashtags": ["ai", "chatgpt", "tech"],
                    "tags": ["why ai cant count rs in strawberry", "chatgpt tokenization", "llm tokens explained"],
                    "pinned_comment": "Did you know AI sees 496, 675, 15717 instead of letters?",
                },
                "tiktok": {
                    "caption": "Why AI can't count the R's in strawberry—it only sees 496, 675, 15717. Did you know this?",
                    "hashtags": ["ai", "chatgpt", "tech", "learnontiktok"],
                    "search_query": "why ai cant count r in strawberry",
                    "comment_hook": "Try asking your AI how many R's are in strawberry right now.",
                },
            },
        }
        with tempfile.TemporaryDirectory() as d:
            p, warns = qareport.write_publish(sb, os.path.join(d, "publish.md"))
            self.assertEqual(warns, [], f"unexpected warnings: {warns}")
            with open(p, encoding="utf-8") as fh:
                txt = fh.read()
            self.assertIn("## 1. YouTube Shorts SEO", txt)
            self.assertIn("## 2. TikTok SEO", txt)
            self.assertIn("YouTube Studio Tags", txt)
            self.assertIn("Pinned Comment", txt)
            self.assertIn("TikTok Search Phrase", txt)

        yt_cap = qareport.render_platform_caption(sb, "youtube_shorts")
        tt_cap = qareport.render_platform_caption(sb, "tiktok")
        self.assertIn("YOUTUBE STUDIO TAGS:", yt_cap)
        self.assertIn("PINNED COMMENT:", yt_cap)
        self.assertIn("TIKTOK SEARCH PHRASE:", tt_cap)
        self.assertNotIn("#shorts", tt_cap.lower())

    def test_split_publish_warns_if_shorts_tag_on_tiktok(self):
        sb = {
            "publish": {
                "youtube_shorts": {
                    "titles": ["Title One", "Title Two", "Title Three"],
                    "description": "Sentence one. Sentence two.",
                    "hashtags": ["science", "physics", "tech"],
                },
                "tiktok": {
                    "caption": "Short punchy TikTok caption?",
                    "hashtags": ["science", "physics", "shorts", "learnontiktok"],
                },
            },
        }
        with tempfile.TemporaryDirectory() as d:
            _, warns = qareport.write_publish(sb, os.path.join(d, "publish.md"))
            self.assertTrue(any("#shorts" in w for w in warns), f"expected #shorts warning, got {warns}")


if __name__ == "__main__":
    unittest.main()
