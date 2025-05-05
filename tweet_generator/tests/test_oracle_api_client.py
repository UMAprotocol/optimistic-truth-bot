#!/usr/bin/env python3
"""
Tests for the Oracle API client
"""

import unittest
import sys
import os
import time
from unittest.mock import patch, MagicMock, call

# Add parent directory to path to import modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from oracle_api_client import OracleApiClient


class TestOracleApiClient(unittest.TestCase):
    """Test the OracleApiClient class"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = OracleApiClient(base_url="https://api.test.example.com")

    @patch('oracle_api_client.requests.Session')
    def test_get_health(self, mock_session):
        """Test getting API health"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {"status": "online", "message": "API is running"}
        mock_session.return_value.get.return_value = mock_response

        # Call the method
        health = self.client.get_health()

        # Verify the call
        mock_session.return_value.get.assert_called_once_with("https://api.test.example.com/")
        self.assertEqual(health, {"status": "online", "message": "API is running"})

    @patch('oracle_api_client.requests.Session')
    def test_query_recent_results(self, mock_session):
        """Test querying recent results"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_session.return_value.get.return_value = mock_response

        # Call the method
        results = self.client.query_recent_results(hours=12, limit=5)

        # Verify the call
        mock_session.return_value.get.assert_called_once()
        call_args = mock_session.return_value.get.call_args[0][0]
        self.assertEqual(call_args, "https://api.test.example.com/api/advanced-query")
        
        # Check parameters
        params = mock_session.return_value.get.call_args[1]['params']
        self.assertEqual(params['limit'], 5)
        self.assertTrue('start_timestamp' in params)
        self.assertTrue('end_timestamp' in params)
        self.assertEqual(params['full'], 'true')
        
        # Check result
        self.assertEqual(results, [{"id": 1}, {"id": 2}])

    @patch('oracle_api_client.requests.Session')
    def test_caching(self, mock_session):
        """Test that results are cached"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_session.return_value.get.return_value = mock_response

        # Call the method twice with the same parameters
        self.client.set_cache_duration(10)  # Set cache duration to 10 seconds
        results1 = self.client.query_recent_results(hours=12, limit=5, cache=True)
        results2 = self.client.query_recent_results(hours=12, limit=5, cache=True)

        # Verify the call was made only once
        mock_session.return_value.get.assert_called_once()
        self.assertEqual(results1, results2)

        # Call with different parameters should make a new request
        mock_session.return_value.get.reset_mock()
        results3 = self.client.query_recent_results(hours=6, limit=5, cache=True)
        mock_session.return_value.get.assert_called_once()

        # Call with cache=False should make a new request
        mock_session.return_value.get.reset_mock()
        results4 = self.client.query_recent_results(hours=12, limit=5, cache=False)
        mock_session.return_value.get.assert_called_once()

    @patch('oracle_api_client.requests.Session')
    def test_get_experiment_results(self, mock_session):
        """Test getting experiment results"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1}, {"id": 2}]
        mock_session.return_value.get.return_value = mock_response

        # Call the method
        results = self.client.get_experiment_results("test_experiment", limit=10)

        # Verify the call
        mock_session.return_value.get.assert_called_once()
        call_args = mock_session.return_value.get.call_args[0][0]
        self.assertEqual(call_args, "https://api.test.example.com/api/experiment/test_experiment")
        
        # Check parameters
        params = mock_session.return_value.get.call_args[1]['params']
        self.assertEqual(params['limit'], 10)
        self.assertEqual(params['full'], 'true')
        
        # Check result
        self.assertEqual(results, [{"id": 1}, {"id": 2}])

    @patch('oracle_api_client.requests.Session')
    def test_get_question_result(self, mock_session):
        """Test getting a question result"""
        # Mock the response
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "test_id", "question": "test_question"}
        mock_session.return_value.get.return_value = mock_response

        # Call the method
        result = self.client.get_question_result("test_question_id")

        # Verify the call
        mock_session.return_value.get.assert_called_once()
        call_args = mock_session.return_value.get.call_args[0][0]
        self.assertEqual(call_args, "https://api.test.example.com/api/question/test_question_id")
        
        # Check parameters
        params = mock_session.return_value.get.call_args[1]['params']
        self.assertEqual(params['full'], 'true')
        
        # Check result
        self.assertEqual(result, {"id": "test_id", "question": "test_question"})

    @patch('oracle_api_client.requests.Session')
    def test_error_handling(self, mock_session):
        """Test error handling"""
        # Mock the response to raise an exception
        mock_session.return_value.get.side_effect = Exception("Test error")

        # Call the method and verify it doesn't raise an exception
        results = self.client.query_recent_results(hours=12, limit=5)
        self.assertEqual(results, [])

        # Call other methods and verify they handle errors gracefully
        result = self.client.get_question_result("test_id")
        self.assertIsNone(result)

        results = self.client.get_experiment_results("test_exp")
        self.assertEqual(results, [])


if __name__ == '__main__':
    unittest.main()