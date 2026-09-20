import type { LucideIcon } from 'lucide-react';
export type ViewId='dashboard'|'trading'|'projects'|'memory'|'browser'|'files'|'voice'|'settings';
export interface NavigationItem{id:ViewId;label:string;icon:LucideIcon;description:string}