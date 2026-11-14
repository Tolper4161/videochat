import Button from "../Button/Button";
import "./NoAccess.css";

interface NoAccessProps {
    isOwner: boolean
}

const content = {
    user: {
        leftBtnText: "Check Again",
        leftBtnBg: "blue-bg",
        rightBtnText: "Return to dashboard",
        message: "Ask the room owner to start a call, or come back later"
    },
    owner: {
        leftBtnText: "Start call",
        leftBtnBg: "green-bg",
        rightBtnText: "Set up a call",
        message: "Start a call when you’re ready"
    }
};

const NoAccess = ({ isOwner }: NoAccessProps) => {
    const { leftBtnText, leftBtnBg, rightBtnText } = content[isOwner ? "owner" : "user"];

    const roomData = {
        title: "Tolper4161 Room"
    };
    
    return (
        <div className="no-access">
            <div className="panel no-access__panel">
                <div className="no-access__content">
                    <div className="no-access__info">
                        <div className="icon icon-missed-call no-access__icon"></div>
                        <div className="no-access__heading">
                            <h1 className="no-access__title">{ roomData.title }</h1>
                            <h2 className="no-access__subtitle">No active call</h2>
                        </div>
                        <div className="no-access__texting">
                            <p className="no-access__text">There is no active call in this room right now</p>
                            <span className="no-access__subtext">Ask the room owner to start a call, or come back later</span>
                        </div>
                    </div>
                    <div className="no-access__btns">
                        <Button className="no-access__btn" background={ leftBtnBg }>{ leftBtnText }</Button>
                        <Button className="no-access__btn" background="gray-bg">{ rightBtnText }</Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default NoAccess;
