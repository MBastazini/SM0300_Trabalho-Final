import unittest
from io import BytesIO
import math
from pathlib import Path


#ARQUIVO CRIADO PELO COPILOT
#PODEMOS NAO USA-LO
from app import app, calculation_cache, DATA_DIR, list_csv_files


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

    def test_model_degree_limit_and_reqm_curve(self):
        response = self.client.get("/api/funcoes/modelos/onix.csv?grau=4")
        self.assertEqual(response.status_code, 400)
        estimate_response = self.client.post(
            "/api/funcoes/estima/onix.csv",
            json={"ano": 2022, "km": 48000, "grau": 4},
        )
        self.assertEqual(estimate_response.status_code, 400)

        response = self.client.get("/api/funcoes/modelos/onix.csv?grau=3")
        payload = response.get_json()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(payload["degree"], 3)
        self.assertEqual(len(payload["polynomial"]["coefficients"]), 10)
        self.assertEqual(payload["reqm_curve"]["degrees"], list(range(31)))
        self.assertEqual(len(payload["reqm_curve"]["values"]), 31)
        self.assertTrue(all(math.isfinite(value) for value in payload["reqm_curve"]["values"]))

    def test_csv_upload_requires_expected_columns(self):
        upload = (BytesIO(b"ano,km\n2024,1000\n"),
                  "missing.csv")
        response = self.client.post(
            "/api/dados/upload",
            data={"file": upload},
            content_type="multipart/form-data",
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("preco", response.get_json()["missing"])

    def test_valid_csv_is_added_and_listed(self):
        csv_name = "teste_upload.csv"
        file_path = DATA_DIR / csv_name
        upload = (BytesIO(b"ano,km,preco\n2024,1000,90000\n2025,500,95000\n"),
                  csv_name)

        try:
            response = self.client.post(
                "/api/dados/upload",
                data={"file": upload},
                content_type="multipart/form-data",
            )

            self.assertEqual(response.status_code, 201)
            self.assertIn(csv_name, list_csv_files())

            # Subir de novo com o mesmo nome não pode sobrescrever o arquivo
            repetido = (BytesIO(b"ano,km,preco\n2020,1,1\n"), csv_name)
            response = self.client.post(
                "/api/dados/upload",
                data={"file": repetido},
                content_type="multipart/form-data",
            )
            self.assertEqual(response.status_code, 409)
            self.assertIn("90000", file_path.read_text(encoding="utf-8"))
        finally:
            if file_path.is_file():
                file_path.unlink()

    def test_validation_uses_curve_from_other_csv(self):
        csv_name = "teste_validacao.csv"
        file_path = DATA_DIR / csv_name
        # O segundo carro tem km acima do máximo do onix.csv: deve ser marcado como fora da faixa
        file_path.write_text("ano,km,preco\n2022,48000,66000\n2023,900000,40000\n", encoding="utf-8")

        try:
            response = self.client.get(f"/api/funcoes/valida/onix.csv?teste={csv_name}&grau=2")
            payload = response.get_json()

            self.assertEqual(response.status_code, 200)
            self.assertEqual(payload["test_count"], 2)
            self.assertEqual(len(payload["rows"]), 2)
            self.assertFalse(payload["rows"][0]["fora_da_faixa"])
            self.assertTrue(payload["rows"][1]["fora_da_faixa"])

            # A previsão tem que ser a mesma do endpoint de estimativa (mesma curva)
            estimate = self.client.post(
                "/api/funcoes/estima/onix.csv",
                json={"ano": 2022, "km": 48000, "grau": 2},
            ).get_json()
            self.assertAlmostEqual(payload["rows"][0]["estimado"], estimate["polynomial"], places=6)

            missing = self.client.get("/api/funcoes/valida/onix.csv?teste=nao_existe.csv")
            self.assertEqual(missing.status_code, 404)
        finally:
            if file_path.is_file():
                file_path.unlink()


if __name__ == "__main__":
    unittest.main()
