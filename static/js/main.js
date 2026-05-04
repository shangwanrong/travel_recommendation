// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 加载热门路线
    loadHotRoutes();

    // 加载省份列表
    loadProvinces();

    // 设置表单提交事件
    setupFormHandlers();

    // 检查登录状态
    checkLoginStatus();
});

// 标记当前显示的是否为推荐路线
let isRecommendedRoutes = false;

// 当前登录用户
let currentUser = null;

// ============ 用户认证 ============

// 检查登录状态
async function checkLoginStatus() {
    try {
        const resp = await fetch('/api/user/info');
        const data = await resp.json();

        const navAuth = document.getElementById('nav-auth');
        const navUserArea = document.getElementById('nav-user-area');

        if (data.user) {
            currentUser = data.user;
            if (navAuth) navAuth.style.display = 'none';
            if (navUserArea) {
                navUserArea.style.display = '';
                document.getElementById('nav-username').textContent = currentUser.username;
                // 首字母作为头像
                const firstChar = currentUser.username.charAt(0).toUpperCase();
                document.getElementById('nav-avatar').textContent = firstChar;
            }
        } else {
            currentUser = null;
            if (navAuth) navAuth.style.display = '';
            if (navUserArea) navUserArea.style.display = 'none';
        }
    } catch (e) {
        console.error('检查登录状态失败:', e);
    }
}

// 显示登录弹窗
function showLoginModal() {
    document.getElementById('authModal').classList.add('show');
}

// 关闭登录弹窗
function closeLoginModal() {
    document.getElementById('authModal').classList.remove('show');
    // 清空错误
    document.getElementById('login-error').style.display = 'none';
    document.getElementById('register-error').style.display = 'none';
}

// 切换登录/注册标签
function switchAuthTab(tab) {
    document.querySelectorAll('.auth-tab').forEach(t => t.classList.remove('active'));
    if (tab === 'login') {
        document.querySelectorAll('.auth-tab')[0].classList.add('active');
        document.getElementById('login-form').style.display = '';
        document.getElementById('register-form').style.display = 'none';
    } else {
        document.querySelectorAll('.auth-tab')[1].classList.add('active');
        document.getElementById('login-form').style.display = 'none';
        document.getElementById('register-form').style.display = '';
    }
    // 清空错误
    document.getElementById('login-error').style.display = 'none';
    document.getElementById('register-error').style.display = 'none';
}

// 处理登录
async function handleLogin(e) {
    e.preventDefault();
    const errorEl = document.getElementById('login-error');
    errorEl.style.display = 'none';

    const username = document.getElementById('login-username').value.trim();
    const password = document.getElementById('login-password').value;

    try {
        const resp = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        const data = await resp.json();

        if (resp.ok) {
            closeLoginModal();
            await checkLoginStatus();
            // 刷新路线卡片（更新收藏按钮状态）
            if (isRecommendedRoutes) {
                const city = document.getElementById('city-select').value;
                const transport = document.getElementById('transport-select').value;
                if (city && transport) {
                    await recommendRoutes(city, transport);
                }
            } else {
                await loadHotRoutes();
            }
        } else {
            errorEl.textContent = data.error || '登录失败';
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请重试';
        errorEl.style.display = 'block';
    }
}

// 处理注册
async function handleRegister(e) {
    e.preventDefault();
    const errorEl = document.getElementById('register-error');
    errorEl.style.display = 'none';

    const username = document.getElementById('reg-username').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value;
    const password2 = document.getElementById('reg-password2').value;

    if (password !== password2) {
        errorEl.textContent = '两次密码输入不一致';
        errorEl.style.display = 'block';
        return;
    }

    try {
        const resp = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, email, password })
        });
        const data = await resp.json();

        if (resp.ok) {
            closeLoginModal();
            await checkLoginStatus();
            if (!isRecommendedRoutes) {
                await loadHotRoutes();
            }
        } else {
            errorEl.textContent = data.error || '注册失败';
            errorEl.style.display = 'block';
        }
    } catch (e) {
        errorEl.textContent = '网络错误，请重试';
        errorEl.style.display = 'block';
    }
}

// 退出登录
async function doLogout() {
    try {
        await fetch('/api/logout', { method: 'POST' });
        currentUser = null;
        await checkLoginStatus();
        if (!isRecommendedRoutes) {
            await loadHotRoutes();
        }
    } catch (e) {
        console.error('退出失败:', e);
    }
}

// ============ 路线加载与展示 ============

// 加载热门路线
async function loadHotRoutes() {
    try {
        const response = await fetch('/api/home');
        const routes = await response.json();
        isRecommendedRoutes = false;
        displayRoutes(routes);
    } catch (error) {
        console.error('加载路线失败:', error);
        document.getElementById('routes-container').innerHTML =
            '<div class="loading">加载失败，请刷新页面重试</div>';
    }
}

// 显示路线卡片
function displayRoutes(routes) {
    const container = document.getElementById('routes-container');

    if (routes.length === 0) {
        container.innerHTML = '<div class="loading">暂无路线</div>';
        return;
    }

    // 批量检查收藏状态
    checkFavoritesBatch(routes.map(r => r.id)).then(favSet => {
        container.innerHTML = routes.map(route => {
            const isFav = favSet.has(route.id);
            return `
            <div class="route-card" onclick="viewRouteDetail('${route.id}', ${isRecommendedRoutes})">
                <button class="route-card-fav ${isFav ? 'favorited' : ''}" onclick="event.stopPropagation(); toggleFavFromCard('${route.id}', this)" title="${isFav ? '取消收藏' : '收藏'}">
                    ${isFav ? '❤️' : '🤍'}
                </button>
                <img src="${route.cover_image}" alt="${route.name}" class="route-card-image" onerror="this.src='https://via.placeholder.com/800x600/89C4F4/FFFFFF?text=${encodeURIComponent(route.city)}'">
                <div class="route-card-content">
                    <div class="route-card-title">${route.name}</div>
                    <div class="route-card-info">
                        <span>📍 ${route.city} · ⏰ ${route.days}天</span>
                        <span class="route-card-price">${route.price_range}</span>
                    </div>
                    <div class="route-card-tags">
                        ${route.tags.map(tag => `<span class="route-tag">${tag}</span>`).join('')}
                    </div>
                </div>
            </div>
        `}).join('');
    });
}

// 批量检查收藏状态
async function checkFavoritesBatch(routeIds) {
    const favSet = new Set();
    if (!currentUser) return favSet;

    try {
        const resp = await fetch('/api/favorites');
        if (resp.ok) {
            const data = await resp.json();
            if (data.favorites) {
                data.favorites.forEach(r => favSet.add(r.id));
            }
        }
    } catch (e) {
        // 静默忽略
    }
    return favSet;
}

// 从卡片收藏/取消收藏
async function toggleFavFromCard(routeId, btn) {
    if (!currentUser) {
        showLoginModal();
        return;
    }

    try {
        const isFav = btn.classList.contains('favorited');

        if (isFav) {
            const resp = await fetch(`/api/favorite/${routeId}`, { method: 'DELETE' });
            if (resp.ok) {
                btn.classList.remove('favorited');
                btn.innerHTML = '🤍';
                btn.title = '收藏';
            }
        } else {
            const resp = await fetch('/api/favorite', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ route_id: routeId })
            });
            if (resp.ok) {
                btn.classList.add('favorited');
                btn.innerHTML = '❤️';
                btn.title = '取消收藏';
            }
        }
    } catch (e) {
        console.error('收藏操作失败:', e);
    }
}

// 加载省份列表
async function loadProvinces() {
    try {
        const response = await fetch('/api/cities');
        const provinces = await response.json();

        const provinceSelect = document.getElementById('province-select');
        provinceSelect.innerHTML = '<option value="">选择省份</option>' +
            provinces.map(prov => `<option value="${prov.name}">${prov.name}</option>`).join('');
    } catch (error) {
        console.error('加载省份失败:', error);
    }
}

// 加载城市列表
async function loadCities(provinceName) {
    try {
        const response = await fetch(`/api/cities?province=${encodeURIComponent(provinceName)}`);
        const cities = await response.json();

        const citySelect = document.getElementById('city-select');
        citySelect.innerHTML = '<option value="">选择城市</option>' +
            cities.map(city => `<option value="${city.id}">${city.name}</option>`).join('');
        citySelect.disabled = false;
    } catch (error) {
        console.error('加载城市失败:', error);
    }
}

// 设置表单处理
function setupFormHandlers() {
    // 省份选择改变
    document.getElementById('province-select').addEventListener('change', function() {
        const province = this.value;
        const citySelect = document.getElementById('city-select');

        if (province) {
            loadCities(province);
        } else {
            citySelect.innerHTML = '<option value="">选择城市</option>';
            citySelect.disabled = true;
        }
    });

    // 表单提交
    document.getElementById('recommend-form').addEventListener('submit', async function(e) {
        e.preventDefault();

        const city = document.getElementById('city-select').value;
        const transport = document.getElementById('transport-select').value;

        if (!city || !transport) {
            alert('请选择省份、城市和出行方式');
            return;
        }

        await recommendRoutes(city, transport);
    });

    // 返回热门按钮
    document.getElementById('back-hot').addEventListener('click', function() {
        isRecommendedRoutes = false;
        loadHotRoutes();
        document.getElementById('section-title').textContent = '🔥 热门路线推荐';
        this.style.display = 'none';
    });
}

// 智能推荐路线
async function recommendRoutes(city, transport) {
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ city, transport })
        });

        const routes = await response.json();

        if (routes.length === 0) {
            document.getElementById('routes-container').innerHTML =
                '<div class="loading">未找到匹配的路线，请尝试其他条件</div>';
        } else {
            isRecommendedRoutes = true;
            displayRoutes(routes);
        }

        // 更新标题，显示出行方式
        const transportText = transport === 'self-driving' ? '🚗 自驾游' : '🚇 公共交通';
        document.getElementById('section-title').textContent = `🎯 为您推荐的路线 (${transportText})`;
        document.getElementById('back-hot').style.display = 'block';

    } catch (error) {
        console.error('推荐失败:', error);
        alert('推荐失败，请重试');
    }
}

// 查看路线详情
function viewRouteDetail(routeId, isCustom = false) {
    // 获取当前选择的出行方式
    const transport = document.getElementById('transport-select')?.value || '';

    if (isCustom) {
        const url = transport ? `/route/${routeId}?custom=1&transport=${transport}` : `/route/${routeId}?custom=1`;
        window.location.href = url;
    } else {
        const url = transport ? `/route/${routeId}?transport=${transport}` : `/route/${routeId}`;
        window.location.href = url;
    }
}

// ============ 用户下拉菜单 ============

// 切换下拉菜单
function toggleUserDropdown() {
    const dropdown = document.getElementById('userDropdown');
    const pill = document.querySelector('.nav-user-pill');
    const isOpen = dropdown.classList.contains('show');

    if (isOpen) {
        dropdown.classList.remove('show');
        pill.classList.remove('open');
    } else {
        dropdown.classList.add('show');
        pill.classList.add('open');
    }
}

// 点击页面其他区域关闭下拉菜单
document.addEventListener('click', function(e) {
    const dropdown = document.getElementById('userDropdown');
    const pill = document.querySelector('.nav-user-pill');
    if (!dropdown || !pill) return;

    if (!e.target.closest('#nav-user-area')) {
        dropdown.classList.remove('show');
        pill.classList.remove('open');
    }
});
