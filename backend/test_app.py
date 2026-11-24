import unittest


#ARQUIVO CRIADO PELO COPILOT
#PODEMOS NAO USA-LO
from app import app, calculation_cache, list_csv_files


class BackendTest(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_connection_endpoint(self):
        response = self.client.get("/api/test")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_data_endpoint_lists_csv_files(self):
        response = self.client.get("/api/dados")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["csv_files"], list_csv_files())

    def test_normalization_and_models_are_cached(self):
        csv_name = "onix.csv"
        calculation_cache.clear()

        normalized_response = self.client.get(f"/api/funcoes/normaliza/{csv_name}")
        models_response = self.client.get(f"/api/funcoes/modelos/{csv_name}")

        first_normalized = calculation_cache.get_normalized(csv_name)
        first_models = calculation_cache.get_models(csv_name)
        second_normalized = calculation_cache.get_normalized(csv_name)
        second_models = calculation_cache.get_models(csv_name)

        self.assertEqual(normalized_response.status_code, 200)
        self.assertEqual(models_response.status_code, 200)
        self.assertIs(first_normalized, second_normalized)
        self.assertIs(first_models, second_models)


if __name__ == "__main__":
    unittest.main()
