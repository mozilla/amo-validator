from validator.main import main

def test_main():
    """Test that `main()` initializes without errors."""
    try:
        main()
    except SystemExit:
        pass
