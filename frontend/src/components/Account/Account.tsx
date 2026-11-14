import "./Account.css";

export interface AccountProps {
    avatarImg: string,
    username: string
}

const Account = ({ avatarImg, username }: AccountProps) => {
    return (
        <div className="account">
            <div className="account__info">
                <img src={ avatarImg } className="account__avatar" />
                <b className="account__username">{ username }</b>
            </div>
            <button className="btn-icon icon icon-wheel account__btn"></button>
        </div>
    );
};

export default Account;
