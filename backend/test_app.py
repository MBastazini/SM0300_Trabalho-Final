import unittest

from app import app, list_csv_files


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


if __name__ == "__main__":
    unittest.main()
