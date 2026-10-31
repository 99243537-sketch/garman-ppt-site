// 把风格库 v2 的 data.js 导出成 JSON，供 build_site_data.py 读取。
// 用法：node export-styles.cjs <design-styles/data.js> <输出.json>
const path = require("path");
const fs = require("fs");
const { STYLES, TERMS } = require(path.resolve(process.argv[2]));
fs.writeFileSync(process.argv[3], JSON.stringify({ STYLES, TERMS }, null, 1));
console.log(`导出 ${STYLES.length} 种风格 → ${process.argv[3]}`);
