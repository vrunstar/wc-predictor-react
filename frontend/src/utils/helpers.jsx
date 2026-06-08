import React from 'react';

export function formatKickoff(kickoffIst) {
  if (!kickoffIst) return 'TBD';
  try {
    // kickoff_ist is stored as IST — extract HH:MM directly from string
    const timePart = String(kickoffIst).split('T')[1];
    if (timePart) return timePart.substring(0, 5);
    return 'TBD';
  } catch (e) {
    return 'TBD';
  }
}

export function stageLabel(stage, group) {
  if (stage === 'group' && group) {
    return `Group ${group}`;
  }
  if (!stage) return '';
  return stage
    .replace(/_/g, ' ')
    .split(' ')
    .map(w => w.charAt(0).toUpperCase() + w.slice(1).toLowerCase())
    .join(' ');
}

export function getFlagUrl(teamCode) {
  if (!teamCode || teamCode === '???') return null;
  return `/flags/${teamCode.toUpperCase()}.png`;
}

export function getPlayerPhotoUrl(photoKey) {
  if (!photoKey) return null;
  return `/players/${photoKey.toLowerCase()}`;
}

export function getStadiumPhotoUrl(photoKey) {
  if (!photoKey) return null;
  return `/stadium/${photoKey}`;
}

export function renderFormSpans(form) {
  if (!form) return <span className="text-[#444]">—</span>;
  const colorMap = { W: 'text-green', D: 'text-gray-400', L: 'text-red-500' };
  
  return (
    <span className="flex items-center gap-[2px]">
      {form.toUpperCase().split('').map((char, idx) => (
        <span 
          key={idx} 
          className={`font-bold text-[0.72rem] select-none ${colorMap[char] || 'text-gray-500'}`}
        >
          {char}
        </span>
      ))}
    </span>
  );
}
