#!/usr/bin/env python3
"""
Path utilities for CLEVA Cantonese Sports & Showbiz project.

Provides functions to get absolute paths to project directories,
replacing hardcoded relative paths throughout the codebase.
"""

import os


def get_project_root():
    """Get the absolute path to the project root directory."""
    # Get the directory containing this file (utils/)
    utils_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(utils_dir))))
    return project_root


def get_data_dir():
    """Get the absolute path to the data directory."""
    return os.path.join(get_project_root(), "data")


def get_soccer_data_dir():
    """Get the absolute path to the soccer data directory."""
    return os.path.join(get_data_dir(), "soccer")


def get_soccer_intermediate_dir():
    """Get the absolute path to the soccer intermediate data directory."""
    return os.path.join(get_soccer_data_dir(), "intermediate")


def get_soccer_output_dir():
    """Get the absolute path to the soccer output directory."""
    return os.path.join(get_soccer_data_dir(), "output")


def get_soccer_raw_dir():
    """Get the absolute path to the soccer raw data directory."""
    return os.path.join(get_soccer_data_dir(), "raw")


def get_cantonese_mapping_dir():
    """Get the absolute path to the cantonese name mapping directory."""
    return os.path.join(get_soccer_data_dir(), "cantonese_name_mapping")


def get_football_players_triples_dir():
    """Get the absolute path to the football players triples directory."""
    return os.path.join(get_soccer_intermediate_dir(), "football_players_triples")


def get_entertainment_data_dir():
    """Get the absolute path to the entertainment data directory."""
    return os.path.join(get_data_dir(), "entertainment")


def get_entertainment_intermediate_dir():
    """Get the absolute path to the entertainment intermediate data directory."""
    return os.path.join(get_entertainment_data_dir(), "intermediate")


def get_entertainment_output_dir():
    """Get the absolute path to the entertainment output directory."""
    return os.path.join(get_entertainment_data_dir(), "output")


def get_entertainment_raw_dir():
    """Get the absolute path to the entertainment raw data directory."""
    return os.path.join(get_entertainment_data_dir(), "raw")


def get_movies_triples_dir():
    """Get the absolute path to the movies triples directory."""
    return os.path.join(get_entertainment_intermediate_dir(), "movie_triples")
