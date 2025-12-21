# Video Sync Feature - 使用說明

## 🚀 快速開始

### 1. 啟動 Dashboard
```bash
./start_dashboard.sh
```

### 2. 開啟 Video Sync 頁面
瀏覽器開啟：http://localhost:8000/video

---

## 📖 功能說明

### 主要功能
- ✅ 視覺化管理所有影片
- ✅ 一鍵同步 metadata 到 YouTube
- ✅ 拖放上傳字幕檔案
- ✅ 批次處理多支影片
- ✅ 自動從 YouTube 取得影片長度和上傳時間
- ✅ 即時顯示同步進度

### 工作流程

#### 單一影片同步
1. **前置作業（YouTube 後台）**
   - 上傳影片檔案
   - 設定封面圖片
   - 設定公開時間
   - 複製 YouTube 連結

2. **填寫 Metadata（Admin Dashboard）**
   - 進入 http://localhost:8000/admin
   - 新增或編輯 Video 記錄
   - 填入 YouTube Link
   - 填入所有必要資訊（標題、描述、Music、Style 等）
   - 儲存

3. **同步到 YouTube（Video Sync 頁面）**
   - 進入 http://localhost:8000/video
   - 找到剛才建立的影片
   - 點擊 "Sync" 按鈕
   - 拖放或選擇 3 個字幕檔案：
     - `ja_subtitle.srt`
     - `en_subtitle.srt`
     - `zh-Hant_subtitle.srt`
   - 點擊 "開始同步"
   - 等待完成（自動重新整理頁面）

4. **自動完成的事項**
   - ✅ 上傳 3 種語言的字幕
   - ✅ 更新影片標題（3 語言）
   - ✅ 更新影片描述（3 語言）
   - ✅ 從 YouTube 取得影片長度
   - ✅ 從 YouTube 取得上傳時間（自動轉換成 UTC+8）
   - ✅ 寫回資料庫

#### 批次處理
1. 勾選多支影片（左側 checkbox）
2. 點擊 "批次同步選中項目"
3. 確認
4. 等待處理完成

⚠️ **注意**：批次處理時，字幕檔案需要事先放在各自的 `temp/{video_id}/` 資料夾中

---

## 🔍 進階說明

### 字幕檔案格式
必須是 `.srt` 格式，檔名必須完全符合：
- `ja_subtitle.srt` - 日文字幕
- `en_subtitle.srt` - 英文字幕
- `zh-Hant_subtitle.srt` - 繁體中文字幕

### 檔案上傳方式
**方法 1：拖放（推薦）**
- 直接從檔案管理器拖曳 3 個檔案到上傳區域

**方法 2：點擊選擇**
- 點擊上傳區域
- 選擇多個檔案（Ctrl/Cmd + 點擊）

### 瀏覽器記憶功能
- 使用 `localStorage` 記住上次上傳的檔案路徑
- 下次開啟會顯示提示
- 加快重複操作速度

### 影片資訊自動更新
系統會自動從 YouTube API 取得：
- **Duration（影片長度）**
  - 格式：ISO 8601（如 `PT3M45S`）
  - 自動轉換成秒數存入資料庫
  - 例如：`PT3M45S` → 225 秒

- **Upload Time（上傳時間）**
  - 格式：ISO 8601（如 `2024-11-16T10:35:49Z`）
  - 自動從 UTC 轉換成 UTC+8（台北時間）
  - 存入資料庫的 `UploadTime` 欄位

---

## 🐛 常見問題

### Q: 點擊 Sync 沒反應？
**A**: 檢查該影片是否有設定 YouTube Link

### Q: 上傳字幕失敗？
**A**: 
- 確認檔案名稱完全正確（區分大小寫）
- 確認是 `.srt` 格式
- 確認檔案沒有損壞

### Q: Sync 卡住不動？
**A**: 
- 檢查網路連線
- 檢查 YouTube API 配額是否用完
- 重新整理頁面重試

### Q: 批次處理部分失敗？
**A**: 
- 檢查失敗的影片是否缺少必要資訊
- 查看瀏覽器 Console 的錯誤訊息
- 個別重新同步失敗的項目

### Q: 影片長度或上傳時間沒有更新？
**A**:
- 確認 YouTube Link 正確
- 確認影片已經成功上傳到 YouTube
- 重新執行 Sync

---

## 🔧 技術細節

### API Endpoints

**GET /video**
- 顯示 Video Sync 管理頁面

**POST /api/upload-subtitles/{video_id}**
- 上傳字幕檔案
- Body: `multipart/form-data` with files
- Response: `{"success": true, "uploaded_files": [...]}`

**POST /api/sync-video/{video_id}**
- 同步單一影片
- Response: `{"success": true, "message": "...", "video_info": {...}}`

**POST /api/batch-sync**
- 批次同步
- Body: `{"video_ids": [1, 2, 3]}`
- Response: `{"success_count": 2, "failed_count": 1, "details": [...]}`

### 資料庫更新
同步完成後，以下欄位會自動更新：
- `Video.Length` - 影片長度（秒）
- `Video.UploadTime` - 上傳時間（UTC+8）

### 暫存檔案
- 字幕檔案暫存在 `temp/{video_id}/` 目錄
- 同步完成後自動刪除
- 如果中途失敗，需要手動清理

---

## 📊 效能建議

### 單一影片
- 處理時間：約 10-30 秒
- 取決於網路速度和字幕檔案大小

### 批次處理
- 每支影片約 10-30 秒
- 依序處理（非並行）
- 10 支影片約需 3-5 分鐘

**建議**：
- 一次不要超過 10 支影片
- 大量處理分批進行
- 避開 YouTube API 使用高峰期

---

## 🎯 後續優化計劃

- [ ] 並行處理批次同步（加快速度）
- [ ] WebSocket 即時進度顯示
- [ ] 失敗自動重試機制
- [ ] 排程定時同步
- [ ] 字幕檔案版本管理
- [ ] 同步歷史記錄查詢

---

有問題或建議？請在 GitHub Issues 回報！
