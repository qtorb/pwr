import "./globals.css";

export const metadata = {
  title: "PWR Next.js Shell",
  description: "Parallel Next.js shell for PWR consuming the FastAPI backend.",
};

export default function RootLayout({ children }) {
  return (
    <html lang="es">
      <body>{children}</body>
    </html>
  );
}
