import React from "react";

const figmaTemplates = [
  {
    title: "Modern Landing Page",
    image: "https://s3-alpha.figma.com/hub/file/3458570/0b1e2b7e-2e2e-4e2e-8e2e-2e2e2e2e2e2e-cover.png",
    url: "https://www.figma.com/community/file/1200195156277806462"
  },
  {
    title: "SaaS Website UI Kit",
    image: "https://s3-alpha.figma.com/hub/file/1122334/1a2b3c4d5e6f7g8h9i0j-cover.png",
    url: "https://www.figma.com/community/file/1166028047678464422"
  },

];

export default function UIRecommendationPage() {
  return (
    <div className="p-8">
      <h1 className="text-2xl font-bold mb-6">Recommended Figma Webpage UI Templates</h1>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {figmaTemplates.map((template) => (
          <a
            key={template.url}
            href={template.url}
            target="_blank"
            rel="noopener noreferrer"
            className="block border rounded-lg overflow-hidden shadow hover:shadow-lg transition"
          >
            <img
              src={template.image}
              alt={template.title}
              className="w-full h-48 object-cover"
            />
            <div className="p-4">
              <h2 className="text-lg font-semibold">{template.title}</h2>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
} 