import gzip
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.sparse import csr_matrix

from scripts.run_experiments import (
    get_refit_data,
    get_tuning_data,
    load_glove_subset,
    mean_embedding_vectors,
)


class GloveSubsetTests(unittest.TestCase):
    def test_loads_only_requested_words_and_averages_vectors(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = Path(temporary_directory) / "vectors.gz"
            with gzip.open(archive_path, "wt", encoding="utf-8") as glove_file:
                glove_file.write("good 1.0 0.0 0.0\n")
                glove_file.write("unused 0.0 1.0 0.0\n")
                glove_file.write("excellent 0.0 0.0 1.0\n")

            embeddings = load_glove_subset(
                archive_path, {"good", "excellent", "missing"}, vector_size=3
            )
            vectors, coverage = mean_embedding_vectors(
                [["good", "excellent"], ["missing"]],
                embeddings,
                vector_size=3,
            )

        self.assertEqual(set(embeddings), {"good", "excellent"})
        np.testing.assert_allclose(vectors[0], [0.5, 0.0, 0.5])
        np.testing.assert_allclose(vectors[1], [0.0, 0.0, 0.0])
        self.assertAlmostEqual(coverage, 2 / 3)

    def test_rejects_vectors_with_wrong_dimension(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            archive_path = Path(temporary_directory) / "vectors.gz"
            with gzip.open(archive_path, "wt", encoding="utf-8") as glove_file:
                glove_file.write("good 1.0 0.0\n")

            with self.assertRaises(ValueError):
                load_glove_subset(archive_path, {"good"}, vector_size=3)


class TuningSampleTests(unittest.TestCase):
    def test_tuning_uses_reproducible_stratified_training_sample(self):
        labels = np.repeat(np.asarray([0, 1], dtype=np.int8), 1550)
        matrix = csr_matrix(np.arange(3100, dtype=np.float32).reshape(-1, 1))

        sample_matrix, sample_labels = get_tuning_data(matrix, labels)
        repeat_matrix, repeat_labels = get_tuning_data(matrix, labels)
        rbf_refit_matrix, rbf_refit_labels = get_refit_data(
            "RBF SVC", matrix, labels
        )
        logistic_refit_matrix, logistic_refit_labels = get_refit_data(
            "Logistic Regression", matrix, labels
        )

        self.assertEqual(sample_matrix.shape[0], 1500)
        self.assertEqual(np.bincount(sample_labels).tolist(), [750, 750])
        np.testing.assert_array_equal(sample_labels, repeat_labels)
        np.testing.assert_array_equal(sample_matrix.toarray(), repeat_matrix.toarray())
        self.assertEqual(rbf_refit_matrix.shape[0], 1500)
        np.testing.assert_array_equal(rbf_refit_labels, sample_labels)
        self.assertEqual(logistic_refit_matrix.shape[0], 3100)
        np.testing.assert_array_equal(logistic_refit_labels, labels)


if __name__ == "__main__":
    unittest.main()
