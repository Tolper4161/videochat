import type { JSX } from "react/jsx-runtime";
import "./PageError.css";

interface PageErrorProps {
    code: number
}

interface IContentData {
    [code: number]: {
        name: string,
        message: JSX.Element,
        btnText: string
    }
}

const content: IContentData = {
    404: {
        name: "Page Not Found",
        message: <>Oops! The page you’re looking for <br className="br-sm" />doesn’t exist or may have been moved</>,
        btnText: "Go to Dashboard"
    },
    500: {
        name: "Internal Server Error",
        message: <>Try refreshing the page or try using the service later</>,
        btnText: "Refresh Page"
    }
};

const PageError = ({ code }: PageErrorProps) => {
    const { name, message, btnText } = content[code];

    return (
        <section className="error">
            <div className="error__content">
                <h1 className="error__code">{ code }</h1>
                <div className="error__info">
                    <div className="error__heading">
                        <h2 className="error__name">{ name }</h2>
                        <p className="error__msg">{ message }</p>
                    </div>
                    <button className="btn blue-bg">{ btnText }</button>
                </div>
            </div>
        </section>
    );
};

export default PageError;
