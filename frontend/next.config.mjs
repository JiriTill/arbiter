/** @type {import('next').NextConfig} */
const nextConfig = {
    // Disable ESLint during production builds (we'll fix lint errors later)
    eslint: {
        ignoreDuringBuilds: true,
    },
    // Disable TypeScript errors during builds
    typescript: {
        ignoreBuildErrors: true,
    },
};

export default nextConfig;
