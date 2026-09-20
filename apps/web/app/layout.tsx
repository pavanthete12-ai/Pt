import type { Metadata } from "next";
import "./globals.css";
export const metadata: Metadata={title:"QuantPulse Live","description":"Market intelligence terminal"};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}