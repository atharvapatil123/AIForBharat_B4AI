"""Validation tests for LLM implementation (syntax and structure)."""

import ast
import pytest
from pathlib import Path


class TestLLMImplementation:
    """Tests to validate LLM implementation structure."""
    
    def test_llm_client_file_exists(self):
        """Test that LLM client file exists."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        assert path.exists(), "LLM client file should exist"
    
    def test_llm_engine_file_exists(self):
        """Test that LLM engine file exists."""
        path = Path("healthcare_insurance_platform/services/llm_engine.py")
        assert path.exists(), "LLM engine file should exist"
    
    def test_llm_client_syntax(self):
        """Test that LLM client has valid Python syntax."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        with open(path) as f:
            code = f.read()
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"LLM client has syntax error: {e}")
    
    def test_llm_engine_syntax(self):
        """Test that LLM engine has valid Python syntax."""
        path = Path("healthcare_insurance_platform/services/llm_engine.py")
        with open(path) as f:
            code = f.read()
        
        try:
            ast.parse(code)
        except SyntaxError as e:
            pytest.fail(f"LLM engine has syntax error: {e}")
    
    def test_llm_client_has_required_classes(self):
        """Test that LLM client defines required classes."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        required_classes = ["LLMProvider", "LLMResponse", "PromptTemplate", "LLMClient"]
        for cls in required_classes:
            assert cls in class_names, f"LLM client should define {cls} class"
    
    def test_llm_engine_has_required_classes(self):
        """Test that LLM engine defines required classes."""
        path = Path("healthcare_insurance_platform/services/llm_engine.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        required_classes = ["ContextDocument", "ContextBundle", "Citation", "EnhancedLLMResponse", "LLMEngine"]
        for cls in required_classes:
            assert cls in class_names, f"LLM engine should define {cls} class"
    
    def test_llm_client_has_generate_method(self):
        """Test that LLMClient has generate method."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        # Find LLMClient class
        llm_client_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "LLMClient":
                llm_client_class = node
                break
        
        assert llm_client_class is not None, "LLMClient class should exist"
        
        # Check for generate method
        method_names = [n.name for n in llm_client_class.body if isinstance(n, ast.AsyncFunctionDef)]
        assert "generate" in method_names, "LLMClient should have generate method"
    
    def test_llm_engine_has_required_methods(self):
        """Test that LLMEngine has required methods."""
        path = Path("healthcare_insurance_platform/services/llm_engine.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        # Find LLMEngine class
        llm_engine_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "LLMEngine":
                llm_engine_class = node
                break
        
        assert llm_engine_class is not None, "LLMEngine class should exist"
        
        # Check for required methods
        method_names = [n.name for n in llm_engine_class.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
        required_methods = ["assemble_context", "generate_response", "generate_from_template"]
        
        for method in required_methods:
            assert method in method_names, f"LLMEngine should have {method} method"
    
    def test_config_has_llm_settings(self):
        """Test that config has LLM settings."""
        path = Path("healthcare_insurance_platform/core/config.py")
        with open(path) as f:
            content = f.read()
        
        required_settings = [
            "llm_provider",
            "openai_api_key",
            "anthropic_api_key",
            "llm_model",
            "llm_temperature",
            "llm_max_tokens",
            "llm_timeout",
            "llm_max_retries",
        ]
        
        for setting in required_settings:
            assert setting in content, f"Config should have {setting} setting"
    
    def test_errors_has_llm_exceptions(self):
        """Test that errors module has LLM exceptions."""
        path = Path("healthcare_insurance_platform/core/errors.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        class_names = [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]
        
        assert "LLMError" in class_names, "Errors should define LLMError"
        assert "LLMProviderError" in class_names, "Errors should define LLMProviderError"
    
    def test_prompt_template_has_format_method(self):
        """Test that PromptTemplate has format method."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        with open(path) as f:
            code = f.read()
        
        tree = ast.parse(code)
        
        # Find PromptTemplate class
        template_class = None
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == "PromptTemplate":
                template_class = node
                break
        
        assert template_class is not None, "PromptTemplate class should exist"
        
        # Check for format method
        method_names = [n.name for n in template_class.body if isinstance(n, ast.FunctionDef)]
        assert "format" in method_names, "PromptTemplate should have format method"
    
    def test_llm_client_has_retry_logic(self):
        """Test that LLM client implements retry logic."""
        path = Path("healthcare_insurance_platform/services/llm_client.py")
        with open(path) as f:
            content = f.read()
        
        # Check for tenacity imports
        assert "from tenacity import" in content, "Should import tenacity for retry logic"
        assert "retry" in content, "Should use retry decorator"
        assert "stop_after_attempt" in content, "Should configure retry attempts"
    
    def test_llm_engine_registers_default_templates(self):
        """Test that LLM engine registers default templates."""
        path = Path("healthcare_insurance_platform/services/llm_engine.py")
        with open(path) as f:
            content = f.read()
        
        # Check for template registration
        assert "_register_default_templates" in content, "Should have method to register default templates"
        assert "policy_comparison" in content, "Should register policy comparison template"
        assert "claim_prediction" in content, "Should register claim prediction template"
    
    def test_env_example_has_llm_config(self):
        """Test that .env.example has LLM configuration."""
        path = Path(".env.example")
        with open(path) as f:
            content = f.read()
        
        required_vars = [
            "LLM_PROVIDER",
            "OPENAI_API_KEY",
            "ANTHROPIC_API_KEY",
            "LLM_MODEL",
            "LLM_TEMPERATURE",
            "LLM_MAX_TOKENS",
            "LLM_TIMEOUT",
            "LLM_MAX_RETRIES",
        ]
        
        for var in required_vars:
            assert var in content, f".env.example should have {var}"
    
    def test_requirements_has_llm_dependencies(self):
        """Test that requirements.txt has LLM dependencies."""
        path = Path("requirements.txt")
        with open(path) as f:
            content = f.read()
        
        required_deps = [
            "langchain",
            "langchain-openai",
            "langchain-anthropic",
            "openai",
            "anthropic",
            "tenacity",
        ]
        
        for dep in required_deps:
            assert dep in content, f"requirements.txt should have {dep}"
