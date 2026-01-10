#!/usr/bin/env python
"""Test Gemini API connectivity and available models.

Usage:
    uv run python scripts/test_gemini.py
    uv run python scripts/test_gemini.py --text-only
    uv run python scripts/test_gemini.py --image-only
"""

import argparse
import os
import sys
import time
from pathlib import Path


def load_env():
    """Load environment variables from .env files."""
    project_root = Path(__file__).parent.parent.parent

    # Load .env first, then .env.secret (secret takes precedence)
    for env_file in [project_root / ".env", project_root / ".env.secret"]:
        if env_file.exists():
            for line in env_file.read_text().splitlines():
                if "=" in line and not line.startswith("#") and line.strip():
                    key, _, value = line.partition("=")
                    key = key.strip()
                    value = value.strip()
                    if value and value != "your_gemini_api_key_here":
                        os.environ[key] = value


def get_client():
    """Get configured Gemini client."""
    from google import genai

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key or api_key == "your_gemini_api_key_here":
        print("❌ GEMINI_API_KEY not set or is placeholder")
        sys.exit(1)

    print(f"✓ API key: {api_key[:8]}...{api_key[-4:]}")
    return genai.Client(api_key=api_key)


def test_text_model(client, model: str) -> bool:
    """Test a text generation model."""
    print(f"\nTesting {model}...")
    try:
        response = client.models.generate_content(
            model=model,
            contents="Respond with exactly: OK"
        )
        result = response.text.strip()
        print(f"  ✓ Response: {result}")
        return True
    except Exception as e:
        print(f"  ❌ Error: {e}")
        return False


def test_image_model(client, model: str, retries: int = 3) -> bool:
    """Test an image generation model with retries."""
    from google.genai import types

    print(f"\nTesting {model}...")

    for attempt in range(retries):
        try:
            response = client.models.generate_content(
                model=model,
                contents="Generate a simple yellow banana icon on white background",
                config=types.GenerateContentConfig(
                    response_modalities=["IMAGE", "TEXT"],
                )
            )

            for part in response.candidates[0].content.parts:
                if hasattr(part, 'inline_data') and part.inline_data is not None:
                    size = len(part.inline_data.data)
                    print(f"  ✓ Image generated! Size: {size} bytes")
                    return True

            print(f"  ⚠ No image in response")
            return False

        except Exception as e:
            error_str = str(e)
            if "503" in error_str or "overloaded" in error_str.lower():
                print(f"  ⚠ Attempt {attempt+1}/{retries}: Model overloaded, retrying...")
                time.sleep(2 * (attempt + 1))
            else:
                print(f"  ❌ Error: {e}")
                return False

    print(f"  ❌ Failed after {retries} attempts")
    return False


def list_models(client):
    """List available Gemini models."""
    print("\nAvailable Gemini models:")
    for model in client.models.list():
        if "gemini" in model.name.lower():
            print(f"  - {model.name}")


def main():
    parser = argparse.ArgumentParser(description="Test Gemini API connectivity")
    parser.add_argument("--text-only", action="store_true", help="Only test text models")
    parser.add_argument("--image-only", action="store_true", help="Only test image models")
    parser.add_argument("--list-models", action="store_true", help="List available models")
    args = parser.parse_args()

    load_env()
    client = get_client()

    if args.list_models:
        list_models(client)
        return

    results = {}

    # Text models
    if not args.image_only:
        text_models = [
            "gemini-2.0-flash",
            "gemini-2.5-pro",
            "gemini-3-pro-preview",
        ]
        print("\n" + "=" * 50)
        print("TEXT MODELS")
        print("=" * 50)
        for model in text_models:
            results[model] = test_text_model(client, model)

    # Image models
    if not args.text_only:
        image_models = [
            "gemini-3-pro-image-preview",
            "gemini-2.5-flash-image-preview",
        ]
        print("\n" + "=" * 50)
        print("IMAGE MODELS")
        print("=" * 50)
        for model in image_models:
            results[model] = test_image_model(client, model)

    # Summary
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    for model, success in results.items():
        status = "✓ Working" if success else "❌ Failed"
        print(f"  {model}: {status}")

    all_passed = all(results.values())
    print()
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
