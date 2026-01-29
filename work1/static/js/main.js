// 主要JavaScript功能

// 专业搜索功能
function filterMajors() {
    const searchInput = document.getElementById('major_search');
    const selectElement = document.getElementById('major_id');
    const searchTerm = searchInput.value.toLowerCase();
    
    // 显示下拉列表
    selectElement.style.display = 'block';
    
    // 遍历所有选项
    for (let i = 0; i < selectElement.options.length; i++) {
        const option = selectElement.options[i];
        const optionText = option.text.toLowerCase();
        
        // 如果是optgroup标签，跳过
        if (option.tagName === 'OPTGROUP') {
            continue;
        }
        
        // 如果选项文本包含搜索词，显示该选项
        if (optionText.includes(searchTerm) || searchTerm === '') {
            option.style.display = 'block';
        } else {
            option.style.display = 'none';
        }
    }
    
    // 如果没有搜索词，隐藏下拉列表
    if (searchTerm === '') {
        selectElement.style.display = 'none';
    }
}

// 选择专业后更新搜索框
document.addEventListener('DOMContentLoaded', function() {
    const majorSelect = document.getElementById('major_id');
    const majorSearch = document.getElementById('major_search');
    
    if (majorSelect && majorSearch) {
        majorSelect.addEventListener('change', function() {
            const selectedOption = this.options[this.selectedIndex];
            
            if (selectedOption.value !== '') {
                majorSearch.value = selectedOption.text;
                this.style.display = 'none';
            }
        });
        
        // 点击搜索框时显示下拉列表
        majorSearch.addEventListener('focus', function() {
            document.getElementById('major_id').style.display = 'block';
        });
        
        // 点击其他地方时隐藏下拉列表
        document.addEventListener('click', function(e) {
            if (!majorSearch.contains(e.target) && !majorSelect.contains(e.target)) {
                majorSelect.style.display = 'none';
            }
        });
    }
});

// 快速筛选功能
function quickFilter(type) {
    const form = document.querySelector('form');
    if (!form) return;
    
    form.reset();
    
    switch(type) {
        case 'male':
            const genderSelect = document.getElementById('gender');
            if (genderSelect) genderSelect.value = '男';
            break;
        case 'female':
            const genderSelect2 = document.getElementById('gender');
            if (genderSelect2) genderSelect2.value = '女';
            break;
        case '4person':
            const capacitySelect = document.getElementById('capacity');
            if (capacitySelect) capacitySelect.value = '4';
            break;
        case '6person':
            const capacitySelect2 = document.getElementById('capacity');
            if (capacitySelect2) capacitySelect2.value = '6';
            break;
        case 'all':
            // 重置所有筛选条件
            form.reset();
            break;
    }
    
    // 自动提交表单
    setTimeout(() => {
        form.submit();
    }, 100);
}

// 选择宿舍功能
function selectDorm(dormId) {
    if (!confirm('确定要选择此宿舍吗？选择后将提交申请。')) {
        return;
    }
    
    window.location.href = `/dorm/${dormId}/select`;
}

// 自动提交表单（当选择改变时）
document.addEventListener('DOMContentLoaded', function() {
    const autoSubmitElements = document.querySelectorAll('select, input[type="checkbox"]');
    autoSubmitElements.forEach(element => {
        element.addEventListener('change', function() {
            // 延迟提交，避免频繁请求
            clearTimeout(this.submitTimeout);
            this.submitTimeout = setTimeout(() => {
                const form = document.querySelector('form');
                if (form) form.submit();
            }, 500);
        });
    });
    
    // 添加滚动到顶部按钮
    const scrollToTopBtn = document.createElement('button');
    scrollToTopBtn.innerHTML = '<i class="bi bi-arrow-up"></i>';
    scrollToTopBtn.className = 'btn btn-primary position-fixed';
    scrollToTopBtn.style.cssText = 'bottom: 20px; right: 20px; z-index: 1000; border-radius: 50%; width: 50px; height: 50px; display: none;';
    scrollToTopBtn.onclick = () => window.scrollTo({ top: 0, behavior: 'smooth' });
    document.body.appendChild(scrollToTopBtn);
    
    // 显示/隐藏滚动按钮
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollToTopBtn.style.display = 'block';
        } else {
            scrollToTopBtn.style.display = 'none';
        }
    });
});
