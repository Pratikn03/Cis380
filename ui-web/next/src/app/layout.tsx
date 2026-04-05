import type { Metadata } from "next";
import { Space_Grotesk, Unbounded } from "next/font/google";
import AppShell from "@/components/AppShell";
import { AuthProvider } from "@/components/auth/AuthProvider";
import GraphQLProvider from "@/components/GraphQLProvider";
import "./globals.css";

const spaceGrotesk = Space_Grotesk({
  variable: "--font-space-grotesk",
  subsets: ["latin"],
});

const unbounded = Unbounded({
  variable: "--font-unbounded",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Sentifargo | Command Center",
  description: "Tier-6 multimodal intelligence platform.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={`${spaceGrotesk.variable} ${unbounded.variable}`}>
        <GraphQLProvider>
          <AuthProvider>
            <AppShell>{children}</AppShell>
          </AuthProvider>
        </GraphQLProvider>
      </body>
    </html>
  );
}
