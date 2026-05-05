# views/__init__.py
# 修正：直接導入整個模組，避免名稱衝突

from . import login_view
from . import admin_view
from . import pt_view
from . import ft_view

# 如果其他地方還需要 login_page 函數，可以保留這行
from .login_view import login_page