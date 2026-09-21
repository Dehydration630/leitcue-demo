export const scenarios = {
  modern: { title:"回声来信", duration:45, description:"一个房间，一封来信。真正的变化，只需要发生一次。", code:"STUDIO / 01", identity:"当代 · 工作室 · 电子音色", suggested:[39], events:[
    {time:0, title:"开场对峙", line:"“这封信，你什么时候收到的？”", reset:false},
    {time:9, title:"镜头转向桌面的信", line:"“先听我把话说完。”", reset:false},
    {time:24, title:"争执暂时缓和", line:"“原来你一直留着它。”", reset:false},
    {time:39, title:"新证据改变主导关系", line:"“但寄信的人，并不是我。”", reset:true}
  ], insight:"同一场景内保持连续；39秒的主导关系重置，才让音乐换一种感觉。"},
  palace: { title:"长廊之后", duration:120, description:"从正殿的对峙，到多年后的重逢。用音乐组织一集的时间。", code:"PALACE / 02", identity:"古风 · 宫廷 · 克制与张力", suggested:[15,90], events:[
    {time:0,title:"正殿对峙",line:"“这道命令，我不能接。”",reset:false},
    {time:15,title:"离开正殿，转入私人谈话",line:"“到了这里，你可以说真话。”",reset:true},
    {time:45,title:"短暂回忆，同一关系仍在延续",line:"“那年，你也这样问过我。”",reset:false},
    {time:90,title:"多年后重逢，身份与情境重置",line:"“这一次，轮到我等你了。”",reset:true}
  ], insight:"15秒与90秒是持续叙事情境变化；45秒的短暂回忆不强制打断音乐。"}
};
export function cap(duration) { return Math.min(12, Math.ceil(duration / 10) - 1); }
export function validate(duration, boundaries) {
  if (!Number.isFinite(duration) || duration < 30 || duration > 180) return "演示支持30–180秒。";
  if (boundaries.some(t => !Number.isFinite(t))) return "请输入有效时间。";
  if (new Set(boundaries).size !== boundaries.length) return "这个位置已经存在。";
  if (boundaries.length + 1 > cap(duration)) return `本集最多${cap(duration)}段，请减少变化位置。`;
  const points = [0, ...[...boundaries].sort((a,b)=>a-b), duration];
  if (points.some((t,i)=>i && t-points[i-1]<5)) return "每段至少5秒，请与前后边界保持距离。";
  return "";
}
export function windows(duration, boundaries) {
  const error = validate(duration,boundaries); if (error) throw new Error(error);
  const points=[0,...[...boundaries].sort((a,b)=>a-b),duration];
  return points.slice(0,-1).map((start,i)=>({start,end:points[i+1]}));
}
export function labelTime(value) { const n=Math.floor(value);return `${String(Math.floor(n/60)).padStart(2,"0")}:${String(n%60).padStart(2,"0")}`; }
