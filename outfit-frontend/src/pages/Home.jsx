import React from "react";
import { Link } from "react-router-dom";

//icon imports
import uploadIcon from "./icons/uploadIcon.png";
import savedIcon from"./icons/heartIcon.png";
import closetIcon from"./icons/closetIcon.png";

export default function Home() {

    const handleUploadClick = () => {
        console.log("Upload clicked");
    };

    const handleClosetClick = () => {
        console.log("Closet clicked");
    };

    const handleSavedClick = () => {
        console.log("Saved clicked");
    };

  return (
    <div style={{ padding: 40, textAlign: 'center' }}>
      <h1>Welcome to Your Virtual Closet!</h1>

      <Link to="/upload" onClick={handleUploadClick}>
        <img src={uploadIcon} alt="Upload" />
      </Link>

      <Link to="/closet" onClick={handleClosetClick}>
        <img src={closetIcon} alt="Closet" />
      </Link>

      <Link to="/saved" onClick={handleSavedClick}>
        <img src={savedIcon} alt="Saved" />
      </Link>
    </div>
  );
}