import { useEffect, useRef, useCallback } from 'react';
import { Box } from '@mui/material';
import { useLocation } from 'react-router-dom';

const SCRIPT_ID = 'google-translate-script';
const SCRIPT_SRC = 'https://translate.google.com/translate_a/element.js?cb=googleTranslateElementInit';

const GoogleTranslate = () => {
  const location = useLocation();
  const boxRef = useRef(null);
  // This callback is called when the Box is attached to the DOM
  const setBoxRef = useCallback((node) => {
    
    boxRef.current = node;

    if (node) {
      // Only add the script if it hasn't been added yet
      if (!document.getElementById(SCRIPT_ID)) {
        const script = document.createElement('script');
        script.id = SCRIPT_ID;
        script.src = SCRIPT_SRC;
        script.async = true;
        document.body.appendChild(script);
      }

      // Always define the init function
      window.googleTranslateElementInit = function () {
        if (window.google && window.google.translate && window.google.translate.TranslateElement) {
          new window.google.translate.TranslateElement(
            {
              pageLanguage: 'en',
              includedLanguages: 'es,fr,ja,ko,zh-CN',
              layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
            },
            'google_translate_element'
          );
        }
      };

      // If the script is already loaded, initialize immediately
      if (window.google && window.google.translate && window.google.translate.TranslateElement) {
        window.googleTranslateElementInit();
      }
    }
  }, [location.pathname]);

  // Re-initialize on every route change
  useEffect(() => {
    if (boxRef.current && window.google && window.google.translate && window.google.translate.TranslateElement) {
      window.googleTranslateElementInit();
    }
  }, [location.pathname]);

  return (
    <Box
      id="google_translate_element"
      ref={setBoxRef}
      sx={{
        position: 'fixed',
        bottom: '20px',
        right: '20px',
        zIndex: 1000,
      }}
    />


    // <Box
    //   // id="google_translate_element"
    //   // ref={setBoxRef}
    //   sx={{
    //     position: 'fixed',
    //     bottom: '20px',
    //     right: '20px',
    //     zIndex: 1000,
    //   }}
    // >Helooo world</Box>
  );
};

export default GoogleTranslate;