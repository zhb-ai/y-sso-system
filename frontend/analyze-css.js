const fs = require('fs');
const path = require('path');

// 递归获取所有文件
function getAllFiles(dir, ext) {
  const files = [];
  const items = fs.readdirSync(dir);
  
  for (const item of items) {
    const fullPath = path.join(dir, item);
    const stat = fs.statSync(fullPath);
    
    if (stat.isDirectory()) {
      files.push(...getAllFiles(fullPath, ext));
    } else if (fullPath.endsWith(ext)) {
      files.push(fullPath);
    }
  }
  
  return files;
}

// 提取 CSS 类名
function extractCssClasses(content) {
  const classes = new Set();
  // 匹配 .classname { 或 .classname, 或 .classname:hover 等
  const regex = /\.([a-zA-Z_-][a-zA-Z0-9_-]*)\s*[{:,]/g;
  let match;
  
  while ((match = regex.exec(content)) !== null) {
    classes.add(match[1]);
  }
  
  return classes;
}

// 检查类是否在文件中使用
function isClassUsed(className, content) {
  // 匹配 class="...classname..." 或 class='...classname...'
  const regex1 = new RegExp(`class=["'][^"']*\\b${className}\\b[^"']*["']`, 'g');
  // 匹配 :class="...classname..."
  const regex2 = new RegExp(`:class=["'][^"']*\\b${className}\\b[^"']*["']`, 'g');
  
  return regex1.test(content) || regex2.test(content);
}

// 主函数
function main() {
  const cssFiles = getAllFiles('src/styles', '.css');
  const vueFiles = getAllFiles('src', '.vue');
  const jsFiles = getAllFiles('src', '.js');
  
  // 收集所有 CSS 类
  const cssClasses = new Map();
  
  for (const file of cssFiles) {
    const content = fs.readFileSync(file, 'utf-8');
    const classes = extractCssClasses(content);
    
    for (const cls of classes) {
      if (!cssClasses.has(cls)) {
        cssClasses.set(cls, { file, used: false });
      }
    }
  }
  
  // 检查使用情况
  const allSourceFiles = [...vueFiles, ...jsFiles];
  
  for (const sourceFile of allSourceFiles) {
    const content = fs.readFileSync(sourceFile, 'utf-8');
    
    for (const [className, info] of cssClasses) {
      if (!info.used && isClassUsed(className, content)) {
        info.used = true;
      }
    }
  }
  
  // 输出结果
  console.log('=== 未使用的 CSS 类 ===\n');
  
  const unusedByFile = new Map();
  
  for (const [className, info] of cssClasses) {
    if (!info.used) {
      const file = info.file;
      if (!unusedByFile.has(file)) {
        unusedByFile.set(file, []);
      }
      unusedByFile.get(file).push(className);
    }
  }
  
  for (const [file, classes] of unusedByFile) {
    console.log(`\n${file}:`);
    for (const cls of classes.sort()) {
      console.log(`  - ${cls}`);
    }
  }
  
  console.log(`\n=== 统计 ===`);
  console.log(`总 CSS 类数: ${cssClasses.size}`);
  console.log(`未使用类数: ${Array.from(cssClasses.values()).filter(v => !v.used).length}`);
  console.log(`使用类数: ${Array.from(cssClasses.values()).filter(v => v.used).length}`);
}

main();
