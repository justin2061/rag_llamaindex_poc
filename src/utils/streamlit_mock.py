"""
Streamlit Mock Module
當 streamlit 不可用時提供基本的 mock 功能
"""

from contextlib import contextmanager
from typing import Any, Dict, List, Optional, Callable
import logging

logger = logging.getLogger(__name__)

class MockSessionState:
    """Mock implementation of Streamlit session state"""
    def __init__(self):
        self._state = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)
    
    def __getitem__(self, key: str) -> Any:
        return self._state[key]
    
    def __setitem__(self, key: str, value: Any) -> None:
        self._state[key] = value
    
    def __contains__(self, key: str) -> bool:
        return key in self._state
    
    def __delitem__(self, key: str) -> None:
        del self._state[key]

class MockColumns:
    """Mock implementation of Streamlit columns"""
    def __init__(self, num_columns: int):
        self.columns = [MockStreamlit() for _ in range(num_columns)]
    
    def __getitem__(self, index: int) -> 'MockStreamlit':
        return self.columns[index]
    
    def __iter__(self):
        return iter(self.columns)

class MockStreamlit:
    """Mock implementation of Streamlit functions"""
    
    def __init__(self):
        self._session_state = MockSessionState()
    
    @property
    def session_state(self) -> MockSessionState:
        return self._session_state
    
    # Display functions
    def write(self, *args, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK WRITE: {args}")
    
    def text(self, body: str) -> None:
        logger.debug(f"STREAMLIT MOCK TEXT: {body}")
    
    def markdown(self, body: str, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK MARKDOWN: {body}")
    
    def title(self, body: str) -> None:
        logger.info(f"TITLE: {body}")
    
    def header(self, body: str) -> None:
        logger.info(f"HEADER: {body}")
    
    def subheader(self, body: str) -> None:
        logger.info(f"SUBHEADER: {body}")
    
    # Status functions
    def info(self, body: str) -> None:
        logger.info(f"INFO: {body}")
    
    def success(self, body: str) -> None:
        logger.info(f"SUCCESS: {body}")
    
    def warning(self, body: str) -> None:
        logger.warning(f"WARNING: {body}")
    
    def error(self, body: str) -> None:
        logger.error(f"ERROR: {body}")
    
    def exception(self, exception) -> None:
        logger.error(f"EXCEPTION: {exception}")
    
    # Progress functions
    @contextmanager
    def spinner(self, text: str = ""):
        logger.info(f"SPINNER START: {text}")
        try:
            yield
        finally:
            logger.info(f"SPINNER END: {text}")
    
    def progress(self, value: float) -> 'MockProgress':
        return MockProgress(value)
    
    # Input functions
    def button(self, label: str, **kwargs) -> bool:
        return False  # Always return False in mock mode
    
    def text_input(self, label: str, value: str = "", **kwargs) -> str:
        return value
    
    def text_area(self, label: str, value: str = "", **kwargs) -> str:
        return value
    
    def selectbox(self, label: str, options: List, index: int = 0, **kwargs) -> Any:
        return options[index] if options else None
    
    def multiselect(self, label: str, options: List, default: List = None, **kwargs) -> List:
        return default or []
    
    def slider(self, label: str, min_value: float, max_value: float, value: float = None, **kwargs) -> float:
        return value if value is not None else min_value
    
    def checkbox(self, label: str, value: bool = False, **kwargs) -> bool:
        return value
    
    def radio(self, label: str, options: List, index: int = 0, **kwargs) -> Any:
        return options[index] if options else None
    
    def file_uploader(self, label: str, **kwargs) -> None:
        return None
    
    # Layout functions
    def columns(self, spec: List[int]) -> MockColumns:
        return MockColumns(len(spec))
    
    def container(self) -> 'MockStreamlit':
        return MockStreamlit()
    
    def expander(self, label: str, expanded: bool = False) -> 'MockStreamlit':
        return MockStreamlit()
    
    def sidebar(self) -> 'MockStreamlit':
        return MockStreamlit()
    
    # Data functions
    def dataframe(self, data: Any, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK DATAFRAME: {type(data)}")
    
    def table(self, data: Any) -> None:
        logger.debug(f"STREAMLIT MOCK TABLE: {type(data)}")
    
    def json(self, body: Any) -> None:
        logger.debug(f"STREAMLIT MOCK JSON: {body}")
    
    # Chart functions
    def line_chart(self, data: Any, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK LINE_CHART: {type(data)}")
    
    def bar_chart(self, data: Any, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK BAR_CHART: {type(data)}")
    
    def plotly_chart(self, figure_or_data: Any, **kwargs) -> None:
        logger.debug(f"STREAMLIT MOCK PLOTLY_CHART: {type(figure_or_data)}")
    
    # Cache functions
    @staticmethod
    def cache_data(func: Callable) -> Callable:
        """Mock cache decorator that does nothing"""
        return func
    
    @staticmethod
    def cache_resource(func: Callable) -> Callable:
        """Mock cache resource decorator that does nothing"""
        return func
    
    # Utility functions
    def rerun(self) -> None:
        logger.debug("STREAMLIT MOCK RERUN")
    
    def stop(self) -> None:
        logger.debug("STREAMLIT MOCK STOP")
    
    def empty(self) -> 'MockEmpty':
        return MockEmpty()

class MockProgress:
    """Mock progress bar"""
    def __init__(self, value: float):
        self.value = value
    
    def progress(self, value: float) -> None:
        self.value = value
        logger.debug(f"PROGRESS: {value}")

class MockEmpty:
    """Mock empty placeholder"""
    def empty(self) -> None:
        pass

# Create global mock instance
mock_st = MockStreamlit()

def get_streamlit():
    """Get streamlit or mock implementation"""
    try:
        import streamlit as st
        return st, True
    except ImportError:
        logger.info("Streamlit not available, using mock implementation")
        return mock_st, False

# For backwards compatibility, export mock as st
st = mock_st
HAS_STREAMLIT = False