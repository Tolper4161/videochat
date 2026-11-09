import type React from 'react';
import './Button.css';

interface IButton {
    className?: string,
    background?: string,
    children: React.ReactNode
}

const Button = ({ className="", background="blue-bg", children } : IButton) => {

    return (
        <button className={ `btn ${ background } ${ className }` }>
            { children }
        </button>
    );
};

export default Button;
