import math
import unittest

import numpy as np

from ngram_lm import EOS, NgramLM, generate

CORPUS = [
    "ala ma kota".split(),
    "kot ma ale".split(),
    "ala ma psa i kota".split(),
    "pies ma ale".split(),
]


class NgramLMTest(unittest.TestCase):
    def test_distributions_sum_to_one(self):
        for method in ["mle", "laplace", "kn"]:
            for n in [1, 2, 3]:
                model = NgramLM(n, method).fit(CORPUS)
                for ctx in [(), ("ma",), ("ala", "ma"), ("xyz", "ma"), ("xyz", "abc")]:
                    p = model.distribution(ctx)
                    if method == "mle" and p.sum() == 0:
                        continue  # nieznany kontekst w MLE
                    self.assertAlmostEqual(p.sum(), 1.0, places=9, msg=(method, n, ctx))

    def test_prob_matches_distribution(self):
        for method in ["mle", "laplace", "kn"]:
            model = NgramLM(3, method).fit(CORPUS)
            p = model.distribution(("ala", "ma"))
            for w in model.vocab:
                self.assertAlmostEqual(model.prob(w, ("ala", "ma")), p[model.index[w]])

    def test_mle_values(self):
        model = NgramLM(2, "mle").fit(CORPUS)
        self.assertAlmostEqual(model.prob("kota", ["ma"]), 1 / 4)
        self.assertAlmostEqual(model.prob("ale", ["ma"]), 2 / 4)

    def test_mle_infinite_perplexity_on_unseen(self):
        model = NgramLM(2, "mle").fit(CORPUS)
        self.assertTrue(math.isinf(model.perplexity([["kot", "ma", "kota"], ["ala", "i"]])["perplexity"]))
        kn = NgramLM(2, "kn").fit(CORPUS)
        self.assertTrue(math.isfinite(kn.perplexity([["ala", "i"]])["perplexity"]))

    def test_generation_is_reproducible(self):
        model = NgramLM(2, "kn").fit(CORPUS)
        a = generate(model, ["ala"], 20, random_seed=1)
        b = generate(model, ["ala"], 20, random_seed=1)
        self.assertEqual(a, b)
        self.assertEqual(sum(1 for t in a[1:] if t != EOS), 20)


if __name__ == "__main__":
    unittest.main()
