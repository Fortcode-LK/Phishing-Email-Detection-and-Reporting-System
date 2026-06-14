const fs = require('fs');
const path = require('path');

const dir = 'c:\\Users\\jkiri\\Documents\\WF Calc\\calculator_app\\tests';
const files = fs.readdirSync(dir).filter(f => f.endsWith('.ts'));

files.forEach(f => {
  const filePath = path.join(dir, f);
  let content = fs.readFileSync(filePath, 'utf-8');
  content = content.replace(/mode:\s*"NORMAL"/g, 'mode: "SUSTAINED_FIRE"');
  content = content.replace(/mode:\s*"RAMPED"/g, 'mode: "SUSTAINED_FIRE"');
  content = content.replace(/mode:\s*"FRESH"/g, 'mode: "FRESH_TARGET"');
  content = content.replace(/combatState:\s*\{\s*\}/g, 'combatState: { stackCounts: {} }');
  content = content.replace(/combatState:\s*\{\s*adaptationStacks/g, 'combatState: { stackCounts: {}, adaptationStacks');
  fs.writeFileSync(filePath, content);
});

console.log("Replaced!");
