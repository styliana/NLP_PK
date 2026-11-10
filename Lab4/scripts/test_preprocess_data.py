import unittest

from nltk.stem import WordNetLemmatizer

from scripts.preprocess_data import ensure_nltk_resource, preprocess_text


class PreprocessTextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        for resource in ("wordnet", "averaged_perceptron_tagger_eng"):
            ensure_nltk_resource(resource)
        cls.lemmatizer = WordNetLemmatizer()

    def test_lowercases_removes_stopwords_and_lemmatizes_verbs(self):
        result = preprocess_text("THE actors were running quickly.", self.lemmatizer)
        self.assertEqual(result, "actor run quickly")

    def test_preserves_negation_and_contrast(self):
        result = preprocess_text("This is not good, but never bad.", self.lemmatizer)
        self.assertEqual(result, "not good but never bad")

    def test_preserves_negated_contractions(self):
        result = preprocess_text("I do n't like it.", self.lemmatizer)
        self.assertEqual(result, "n't like")

    def test_rejects_text_without_tokens(self):
        with self.assertRaises(ValueError):
            preprocess_text("!!! 123", self.lemmatizer)

    def test_retains_sentence_when_every_token_is_a_stopword(self):
        result = preprocess_text("everything is off", self.lemmatizer)
        self.assertEqual(result, "everything be off")


if __name__ == "__main__":
    unittest.main()
