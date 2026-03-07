// オートコンプリート機能
document.addEventListener('DOMContentLoaded', function() {
    // ヘッダーの検索入力
    const headerInput = document.getElementById('search-input');
    // ホームページの検索入力
    const homeInput = document.querySelector('input[name="q"]');
    
    // 両方の検索入力に対して処理
    const inputs = [headerInput, homeInput].filter(Boolean);
    
    inputs.forEach(input => {
        // 候補箱を作成
        const suggestBox = document.createElement('div');
        suggestBox.className = 'suggest-box';
        suggestBox.style.display = 'none';
        input.parentElement.style.position = 'relative';
        input.parentElement.appendChild(suggestBox);
        
        let timeout;
        
        // 入力イベント
        input.addEventListener('input', async function() {
            clearTimeout(timeout);
            
            const query = this.value.trim();
            if (query.length < 2) {
                suggestBox.style.display = 'none';
                return;
            }
            
            // サーバーから候補を取得
            timeout = setTimeout(async () => {
                try {
                    const response = await fetch(`/api/suggestions?q=${encodeURIComponent(query)}`);
                    const suggestions = await response.json();
                    
                    if (suggestions.length === 0) {
                        suggestBox.style.display = 'none';
                        return;
                    }
                    
                    // 候補を表示
                    suggestBox.innerHTML = suggestions
                        .map(s => `<div class="suggest-item">${escapeHtml(s)}</div>`)
                        .join('');
                    
                    // 位置を調整
                    const rect = input.getBoundingClientRect();
                    suggestBox.style.left = (rect.left - input.parentElement.getBoundingClientRect().left) + 'px';
                    suggestBox.style.top = (rect.bottom - input.parentElement.getBoundingClientRect().top) + 'px';
                    suggestBox.style.width = rect.width + 'px';
                    suggestBox.style.display = 'block';
                    
                    // 候補をクリックしたら値をセット
                    document.querySelectorAll('.suggest-item').forEach(item => {
                        item.addEventListener('click', function() {
                            input.value = this.innerText;
                            suggestBox.style.display = 'none';
                            input.form.submit();
                        });
                    });
                } catch (error) {
                    console.error('検索候補の取得に失敗:', error);
                    suggestBox.style.display = 'none';
                }
            }, 300);
        });
        
        // フォーカス時に候補を表示
        input.addEventListener('focus', async function() {
            if (this.value.length >= 2) {
                // 既に候補がある場合は表示
                if (suggestBox.innerHTML) {
                    suggestBox.style.display = 'block';
                }
            }
        });
        
        // クリック外で候補を隠す
        document.addEventListener('click', function(e) {
            if (e.target !== input && !suggestBox.contains(e.target)) {
                suggestBox.style.display = 'none';
            }
        });
    });
    
    // HTML特殊文字をエスケープ
    function escapeHtml(text) {
        const map = {
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#039;'
        };
        return text.replace(/[&<>"']/g, m => map[m]);
    }
});
