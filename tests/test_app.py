"""Tests for `datapm_studio.app` CLI argument parsing."""

from __future__ import annotations

from unittest.mock import patch

import pytest

from datapm_studio.app import _build_arg_parser, main


class TestArgParser:
    def test_defaults(self):
        args = _build_arg_parser().parse_args([])
        assert args.host == "127.0.0.1"
        assert args.port == 5555

    def test_port_override(self):
        args = _build_arg_parser().parse_args(["--port", "5556"])
        assert args.port == 5556

    def test_host_override(self):
        args = _build_arg_parser().parse_args(["--host", "0.0.0.0"])
        assert args.host == "0.0.0.0"

    def test_port_requires_int(self):
        with pytest.raises(SystemExit):
            _build_arg_parser().parse_args(["--port", "not-a-number"])


class TestMain:
    def test_main_passes_args_to_app_run(self):
        with patch("datapm_studio.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            main(["--port", "6000", "--host", "0.0.0.0"])
            mock_app.run.assert_called_once_with(host="0.0.0.0", port=6000, debug=False)

    def test_main_defaults(self):
        with patch("datapm_studio.app.create_app") as mock_create:
            mock_app = mock_create.return_value
            main([])
            mock_app.run.assert_called_once_with(
                host="127.0.0.1", port=5555, debug=False
            )
