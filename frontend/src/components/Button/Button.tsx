import type React from 'react';
import './Button.css';

interface IButton {
    className?: string,
    background?: string,
    icon?: string,
    children: React.ReactNode
}

const Button = ({ className="", background="blue-bg", icon="", children } : IButton) => {

    return (
        <button className={ `btn ${ icon ? "icon " + icon : "" } ${ background } ${ className }` }>
            { children }
        </button>
    );
};

export default Button;
