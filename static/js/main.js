// 页面加载完成后执行
document.addEventListener('DOMContentLoaded', function() {
    // 加载热门路线
    loadHotRoutes();

    // 加载省份列表
    loadProvinces();

    // 设置表单提交事件
    setupFormHandlers();
});

// 标记当前显示的是否为推荐路线
let isRecommendedRoutes = false;

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

    container.innerHTML = routes.map(route => `
        <div class="route-card" onclick="viewRouteDetail('${route.id}', ${isRecommendedRoutes})">
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
    `).join('');
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
        const days = parseInt(document.getElementById('days-select').value);
        const transport = document.getElementById('transport-select').value;

        if (!city || !days || !transport) {
            alert('请选择省份、城市、旅游天数和出行方式');
            return;
        }

        await recommendRoutes(city, days, transport);
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
async function recommendRoutes(city, days, transport) {
    try {
        const response = await fetch('/api/recommend', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ city, days, transport })
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
